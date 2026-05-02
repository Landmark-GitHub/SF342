import torch
import numpy as np
import pandas as pd
import re
from tqdm import tqdm
import ahocorasick


# =========================================================
# TEXT
# =========================================================
def normalize_text(text):

    if pd.isna(text):
        return ""

    text = str(text).lower()

    text = re.sub(r"[^a-z0-9\s\-_]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    return text


# =========================================================
# AUTHOR PROCESS
# =========================================================
def process_scopus_authors(df):

    df = df.copy()

    # -----------------------------------------------------
    # corresponding
    # -----------------------------------------------------
    def extract_corr_name(corr_text):

        if pd.isna(corr_text):
            return None

        corr_text = str(corr_text)

        if ";" not in corr_text:
            return None

        first_part = corr_text.split(";")[0].strip()

        if "." not in first_part:
            return None

        parts = first_part.split(".")

        if len(parts) < 2:
            return None

        return f"{parts[1].strip()}, {parts[0].strip()}"

    df["_corr_name"] = df["Correspondence Address"].apply(extract_corr_name)

    # -----------------------------------------------------
    # split columns
    # -----------------------------------------------------
    def split_col(col):

        return (
            df[col]
            .fillna("")
            .astype(str)
            .str.split(";")
            .apply(lambda x: [a.strip() for a in x if a.strip()])
        )

    df["_authors_full"] = split_col("Author full names")
    df["_authors_short"] = split_col("Authors")
    df["_affiliations"] = split_col("Affiliations")

    # -----------------------------------------------------
    # explode
    # -----------------------------------------------------
    df_exp = df.explode("_authors_full").copy()

    df_exp["_author_order"] = (
        df_exp.groupby(level=0).cumcount()
    )

    # -----------------------------------------------------
    # parse author
    # -----------------------------------------------------
    pattern = re.compile(r"(.+?)\s*\((\d+)\)")

    def parse_author(a):

        a = str(a) if pd.notna(a) else ""

        m = pattern.match(a)

        if m:
            full = m.group(1).strip()
            aid = m.group(2)
        else:
            full = a
            aid = None

        if "," in full:
            last, first = [x.strip() for x in full.split(",", 1)]
            name = f"{first} {last}"
        else:
            name = full

        return name, aid

    parsed = df_exp["_authors_full"].apply(parse_author)

    df_exp["name"] = parsed.str[0]
    df_exp["name_id"] = parsed.str[1]

    # -----------------------------------------------------
    # author order
    # -----------------------------------------------------
    df_exp["author_order"] = df_exp["_author_order"] + 1

    df_exp["first_author"] = (
        df_exp["_author_order"] == 0
    ).astype(int)

    # -----------------------------------------------------
    # affiliation
    # -----------------------------------------------------
    def get_profile(row):

        affs = row["_affiliations"]
        i = row["_author_order"]

        if isinstance(affs, list) and i < len(affs):
            return affs[i]

        return None

    df_exp["profile"] = df_exp.apply(get_profile, axis=1)

    # -----------------------------------------------------
    # corresponding
    # -----------------------------------------------------
    def check_corresponding(row):

        cn = row["_corr_name"]

        shorts = row["_authors_short"]

        i = row["_author_order"]

        if not isinstance(shorts, list):
            return 0

        if i >= len(shorts):
            return 0

        s = shorts[i]

        cn = "" if pd.isna(cn) else str(cn).strip()
        s = "" if pd.isna(s) else str(s).strip()

        if not cn or not s:
            return 0

        return int(s.startswith(cn))

    df_exp["corresponding"] = (
        df_exp.apply(check_corresponding, axis=1)
    )

    keep = [
        "EID",
        "name",
        "name_id",
        "profile",
        "author_order",
        "first_author",
        "corresponding",
        "Title",
        "Abstract",
        "Author Keywords",
        "Index Keywords"
    ]

    return df_exp[keep].reset_index(drop=True)


# =========================================================
# AHO
# =========================================================
def build_ac_automaton(df_tax):

    A = ahocorasick.Automaton()

    for idx, kw in enumerate(df_tax["keyword_norm"].tolist()):

        if kw:
            A.add_word(f" {kw} ", (idx, kw))

    A.make_automaton()

    return A


# =========================================================
# MAP EID
# =========================================================
def map_eid_to_taxonomy(
    df_scopus,
    model,
    df_tax,
    tax_emb_matrix
):

    device = "cuda" if torch.cuda.is_available() else "cpu"

    tax_rows = df_tax.to_dict("records")

    A = build_ac_automaton(df_tax)

    source_weights_map = {
        "Author Keywords": 4.0,
        "Index Keywords": 3.5,
        "Title": 3.0,
        "Abstract": 1.5
    }

    df_papers = (
        df_scopus
        .drop_duplicates(subset=["EID"])
        .reset_index(drop=True)
    )

    # -----------------------------------------------------
    # paper text
    # -----------------------------------------------------
    def make_text(row):

        return normalize_text(
            " ".join([
                str(row.get("Title", "")),
                str(row.get("Author Keywords", "")),
                str(row.get("Index Keywords", ""))
            ])
        )

    raw_texts = df_papers.apply(make_text, axis=1).tolist()

    texts_norm = [f" {t} " for t in raw_texts]

    parts_df = pd.DataFrame({
        k: df_papers[k].fillna("").apply(normalize_text)
        for k in source_weights_map.keys()
    })

    parts_list = parts_df.to_dict("records")

    # -----------------------------------------------------
    # encode paper
    # -----------------------------------------------------
    paper_embs = model.encode(
        raw_texts,
        batch_size=512,
        show_progress_bar=True,
        convert_to_tensor=True,
        device=device,
        normalize_embeddings=True
    )

    results = []

    for row_i in tqdm(range(len(df_papers))):

        row = df_papers.iloc[row_i]

        paper_emb = paper_embs[row_i]

        matched = {}

        for _, (tax_idx, kw) in A.iter(texts_norm[row_i]):

            sw = max(
                (
                    w
                    for f, w in source_weights_map.items()
                    if kw in parts_list[row_i][f]
                ),
                default=0.0
            )

            if sw > matched.get(tax_idx, 0):
                matched[tax_idx] = sw

        if not matched:
            continue

        indices = list(matched.keys())

        sims = torch.mv(
            tax_emb_matrix[indices],
            paper_emb
        ).cpu().numpy()

        for j, tax_idx in enumerate(indices):

            sim = float(sims[j])

            if sim < 0:
                continue

            tr = tax_rows[tax_idx]

            results.append({
                "EID": row["EID"],
                "taxonomy_id": tr["taxonomy_id"],
                "l1_field": tr["l1_field"],
                "l2_domain": tr["l2_domain"],
                "subfield_name": tr["subfield_name"],
                "similarity": sim,
                "source_weight": matched[tax_idx],
                "keyword_weight": tr["keyword_weight"],
                "match_priority": tr["match_priority"],
                "keyword_type": tr["keyword_type"]
            })

    return pd.DataFrame(results)


# =========================================================
# MERGE SCORE
# =========================================================
def merge_and_score(df_authors, df_eid_tax):

    df = df_authors.merge(df_eid_tax, on="EID")

    kw_type_w = {
        "exact_or_near_exact": 1.2,
        "token_or_phrase_expansion": 1.0,
        "domain_seed": 0.8
    }

    df["paper_topic_score"] = (
        df["keyword_weight"]
        * df["match_priority"]
        * df["keyword_type"].map(kw_type_w).fillna(0.7)
        * df["source_weight"]
    )

    role_w = np.select(
        [
            df["first_author"] == 1,
            df["corresponding"] == 1
        ],
        [1.0, 0.7],
        default=0.2
    )

    df["expertise_score"] = (
        df["paper_topic_score"] * role_w
    )

    return df


# =========================================================
# MAIN PIPELINE
# =========================================================
def mapping_hybrid(
    df_scopus,
    model,
    df_tax,
    tax_emb_matrix
):

    df_eid_tax = map_eid_to_taxonomy(
        df_scopus=df_scopus,
        model=model,
        df_tax=df_tax,
        tax_emb_matrix=tax_emb_matrix
    )

    df_authors = process_scopus_authors(df_scopus)

    df_final = merge_and_score(
        df_authors,
        df_eid_tax
    )

    return df_final




# import time
# import torch
# import numpy as np
# import pandas as pd
# import re
# from tqdm import tqdm
# import ahocorasick


# def normalize_text(text):
#     if pd.isna(text):
#         return ""
#     text = str(text).lower()
#     text = re.sub(r"[^a-z0-9\s\-_]", " ", text)
#     text = re.sub(r"\s+", " ", text).strip()
#     return text

# # ─── process_scopus_authors: vectorized แทน iterrows ────────────────────────
# def process_scopus_authors(df):

#     df = df.copy()
#     tqdm.pandas(desc="Step 2/3: parse authors")

#     # ── corresponding name ──────────────────────────────────────────────────
#     def extract_corr_name(corr_text):
#         if not corr_text or ";" not in str(corr_text):
#             return None
#         first_part = str(corr_text).split(";")[0].strip()
#         if "." not in first_part:
#             return None
#         parts = first_part.split(".")
#         return f"{parts[1].strip()}, {parts[0].strip()}"

#     df["_corr_name"] = df["Correspondence Address"].apply(extract_corr_name)

#     # ── explode authors ──────────────────────────────────────────────────────
#     def split_col(col):
#         return df[col].fillna("").str.split(";").apply(
#             lambda x: [a.strip() for a in x if a.strip()]
#         )

#     df["_authors_full"] = split_col("Author full names")
#     df["_authors_short"] = split_col("Authors")
#     df["_affiliations"] = split_col("Affiliations")

#     # explode บน authors_full
#     df_exp = df.explode("_authors_full").copy()
#     df_exp["_author_order"] = df_exp.groupby(level=0).cumcount()

#     # ── parse full name + author_id ─────────────────────────────────────────
#     pattern = re.compile(r"(.+?)\s*\((\d+)\)")

#     def parse_author(a):
#         a = str(a) if pd.notna(a) else ""
#         m = pattern.match(a)
#         if m:
#             full, aid = m.group(1).strip(), m.group(2)
#         else:
#             full, aid = a, None
#         if "," in full:
#             last, first = [x.strip() for x in full.split(",", 1)]
#             name = f"{first} {last}"
#         else:
#             name = full
#         return pd.Series({"name": name, "name_id": aid})

#     parsed = df_exp["_authors_full"].progress_apply(parse_author)
#     df_exp["name"] = parsed["name"]
#     df_exp["name_id"] = parsed["name_id"]

#     # ── author_order, first_author ──────────────────────────────────────────
#     df_exp["author_order"] = df_exp["_author_order"] + 1
#     df_exp["first_author"] = (df_exp["_author_order"] == 0).astype(int)

#     # ── profile (affiliation) ────────────────────────────────────────────────
#     def get_profile(row):
#         affs = row["_affiliations"]
#         i = row["_author_order"]
#         return affs[i] if isinstance(affs, list) and i < len(affs) else None

#     df_exp["profile"] = df_exp.progress_apply(get_profile, axis=1)

#     # ── corresponding ────────────────────────────────────────────────────────
#     def check_corresponding(row):
#         cn = row["_corr_name"]
#         if not cn or pd.isna(cn):
#             return 0
#         shorts = row["_authors_short"]
#         i = row["_author_order"]
#         if isinstance(shorts, list) and i < len(shorts):
#             short_name = shorts[i]
#             if pd.isna(short_name):
#                 return 0
#             return 1 if str(short_name).startswith(str(cn)) else 0
#         return 0

#     df_exp["corresponding"] = df_exp.progress_apply(check_corresponding, axis=1)

#     # ── clean output ─────────────────────────────────────────────────────────
#     keep = ["EID", "name", "name_id", "profile", "author_order",
#             "first_author", "corresponding",
#             "Title", "Abstract", "Author Keywords", "Index Keywords"]

#     return df_exp[keep].reset_index(drop=True)


# def build_ac_automaton(df_tax):
#     A = ahocorasick.Automaton()
#     for idx, kw in enumerate(df_tax["keyword_norm"].tolist()):
#         if kw:
#             A.add_word(f" {kw} ", (idx, kw))
#     A.make_automaton()
#     return A


# def map_eid_to_taxonomy(df_scopus, df_tax, model, tax_emb_matrix):
#     device = getattr(model, "device", "cuda" if torch.cuda.is_available() else "cpu")
#     model.to(device)

#     tax_rows_list = df_tax.to_dict("records")

#     print("Building Aho-Corasick automaton...")
#     A = build_ac_automaton(df_tax)

#     source_weights_map = {
#         "Author Keywords": 4.0,
#         "Index Keywords":  3.5,
#         "Title":           3.0,
#         "Abstract":        1.5
#     }

#     df_papers = df_scopus.drop_duplicates(subset=["EID"]).reset_index(drop=True)

#     # ── vectorized text prep ─────────────────────────────────────────────────
#     def make_text(row):
#         return normalize_text(" ".join([
#             str(row.get("Title", "")),
#             str(row.get("Author Keywords", "")),
#             str(row.get("Index Keywords", ""))
#         ]))

#     print("Preparing paper texts...")
#     raw_texts = df_papers.apply(make_text, axis=1).tolist()
#     texts_norm = [f" {t} " for t in raw_texts]

#     parts_df = pd.DataFrame({
#         k: df_papers[k].fillna("").apply(normalize_text)
#         for k in source_weights_map.keys()
#     })
#     parts_list = parts_df.to_dict("records")

#     print(f"Encoding {len(df_papers)} unique papers...")
#     paper_embs = model.encode(
#         raw_texts,
#         batch_size=512,
#         show_progress_bar=True,
#         convert_to_tensor=True,
#         device=device,
#         normalize_embeddings=True
#     )

#     # ── precompute source weight lookup ──────────────────────────────────────
#     # สร้าง tax_idx → field weight dict ไว้ล่วงหน้า
#     sw_fields = list(source_weights_map.keys())
#     sw_vals   = list(source_weights_map.values())

#     results = []

#     pbar = tqdm(
#         range(len(df_papers)),
#         total=len(df_papers),
#         desc=f"🚀 Mapping EID on {str(device).upper()}"
#     )

#     for row_i in pbar:

#         row       = df_papers.iloc[row_i]
#         pbar.set_postfix({"EID": str(row["EID"])[:20]}, refresh=True)

#         text_norm_padded = texts_norm[row_i]
#         parts            = parts_list[row_i]
#         paper_emb        = paper_embs[row_i]

#         # AC search — เก็บ max source_weight ต่อ tax_idx
#         matched: dict[int, float] = {}
#         for _, (tax_idx, kw) in A.iter(text_norm_padded):
#             sw = max(
#                 (w for f, w in zip(sw_fields, sw_vals) if kw in parts[f]),
#                 default=0.0
#             )
#             if sw > matched.get(tax_idx, 0.0):
#                 matched[tax_idx] = sw

#         if not matched:
#             continue

#         indices  = list(matched.keys())
#         sw_list  = [matched[i] for i in indices]

#         # vectorized cosine (dot product เพราะ normalize แล้ว)
#         sims_np = torch.mv(tax_emb_matrix[indices], paper_emb).cpu().numpy()

#         eid = row["EID"]

#         for j in range(len(indices)):
#             sim_val = float(sims_np[j])
#             if sim_val < 0.0:
#                 continue
#             tr = tax_rows_list[indices[j]]
#             results.append((
#                 eid,
#                 tr["taxonomy_id"],
#                 tr["l1_field"],
#                 tr["l2_domain"],
#                 tr["subfield_name"],
#                 tr["keyword"],
#                 tr["keyword_norm"],
#                 tr["keyword_type"],
#                 tr["keyword_rank_within_subfield"],
#                 tr["match_priority"],
#                 tr["keyword_weight"],
#                 sw_list[j],
#                 sim_val
#             ))

#     # ── สร้าง DataFrame จาก list of tuples (เร็วกว่า list of dicts ~3×) ─────
#     cols = [
#         "EID", "taxonomy_id", "l1_field", "l2_domain", "subfield_name",
#         "keyword", "keyword_norm", "keyword_type",
#         "keyword_rank_within_subfield", "match_priority", "keyword_weight",
#         "source_weight", "similarity"
#     ]
#     return pd.DataFrame(results, columns=cols)


# def mapping_hybrid(df_scopus, df_tax, model, tax_embeddings):
#     t0 = time.time()

#     print("=" * 50)
#     print("Step 1: map EID -> taxonomy")
#     print("=" * 50)
#     df_eid_tax = map_eid_to_taxonomy(df_scopus, df_tax, model, tax_embeddings)
#     t1 = time.time()
#     print(f"Step 1 done: {t1 - t0:.1f}s | {len(df_eid_tax):,} rows\n")

#     print("=" * 50)
#     print("Step 2: process scopus authors")
#     print("=" * 50)
#     df_authors = process_scopus_authors(df_scopus)
#     t2 = time.time()
#     print(f"Step 2 done: {t2 - t1:.1f}s | {len(df_authors):,} rows\n")

#     print("=" * 50)
#     print("Step 3: merge + score")
#     print("=" * 50)
#     df_final = merge_and_score(df_authors, df_eid_tax)
#     t3 = time.time()
#     print(f"Step 3 done: {t3 - t2:.1f}s | {len(df_final):,} rows\n")

#     print("=" * 50)
#     print(f"Total: {t3 - t0:.1f}s ({(t3 - t0) / 60:.1f} min)")
#     print("=" * 50)

#     metrics = {
#         "step1_seconds": round(t1 - t0, 3),
#         "step2_seconds": round(t2 - t1, 3),
#         "step3_seconds": round(t3 - t2, 3),
#         "total_seconds": round(t3 - t0, 3),
#         "step1_rows": int(len(df_eid_tax)),
#         "step2_rows": int(len(df_authors)),
#         "step3_rows": int(len(df_final)),
#     }

#     return df_final, metrics


# def merge_and_score(df_authors, df_eid_tax):

#     df = df_authors.merge(df_eid_tax, on="EID", how="inner")

#     kw_type_w = {
#         "exact_or_near_exact":       1.2,
#         "token_or_phrase_expansion": 1.0,
#         "domain_seed":               0.8
#     }

#     df["paper_topic_score"] = (
#         df["keyword_weight"] *
#         df["match_priority"] *
#         df["keyword_type"].map(kw_type_w).fillna(0.7) *
#         df["source_weight"]
#     )

#     role_w = np.select(
#         [df["first_author"] == 1, df["corresponding"] == 1],
#         [1.0, 0.7],
#         default=0.2
#     )
#     df["expertise_score"] = df["paper_topic_score"] * role_w

#     df_final = df.groupby(
#         ["name_id", "name", "taxonomy_id", "l1_field", "l2_domain", "subfield_name"]
#     ).agg(
#         expertise_score      = ("expertise_score", "sum"),
#         paper_count          = ("EID", "nunique"),
#         profile             = ("profile", lambda x: next((str(v) for v in x if pd.notna(v) and str(v).strip()), "")),
#         first_author_papers  = ("first_author", "sum"),
#         corresponding_papers = ("corresponding", "sum"),
#         author_papers        = ("EID", "count"),
#         avg_similarity       = ("similarity", "mean"),
#         evidence_paper_ids   = ("EID",   lambda x: list(set(x))),
#         evidence_titles      = ("Title", lambda x: list(set(x)))
#     ).reset_index().rename(columns={"name_id": "author_id", "name": "author_name"})

#     frontend_cols = [
#         "author_id", "author_name", "taxonomy_id", "l1_field", "l2_domain",
#         "subfield_name", "expertise_score", "paper_count", "avg_similarity", "profile"
#     ]
#     extra_cols = [c for c in df_final.columns if c not in frontend_cols]
#     return df_final[frontend_cols + extra_cols]