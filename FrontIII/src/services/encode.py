# from sentence_transformers import SentenceTransformer
# import torch
# import numpy as np
# import pandas as pd
# import re
# from tqdm import tqdm
# import ahocorasick

# # ── compile regex ครั้งเดียว ──────────────────────────────────────────────────
# _RE_CLEAN  = re.compile(r"[^a-z0-9\s\-_]")
# _RE_SPACE  = re.compile(r"\s+")

# def normalize_text(text):
#     if pd.isna(text):
#         return ""
#     text = str(text).lower()
#     text = _RE_CLEAN.sub(" ", text)
#     text = _RE_SPACE.sub(" ", text).strip()
#     return text

# def normalize_series(s: pd.Series) -> pd.Series:
#     return (
#         s.fillna("")
#          .str.lower()
#          .str.replace(_RE_CLEAN, " ", regex=True)
#          .str.replace(_RE_SPACE, " ", regex=True)
#          .str.strip()
#     )

# def process_scopus_authors(df):
#     # ป้องกันการแก้ไขข้อมูลใน DataFrame ต้นฉบับ
#     df = df.copy()

#     # 1. จัดการข้อมูล Correspondence Address เพื่อหาตัวผู้เขียนหลัก (Corresponding Author)
#     corr = df["Correspondence Address"].fillna("")
#     has_semi = corr.str.contains(";", regex=False)
#     first_part = corr.str.split(";").str[0].str.strip()
#     has_dot = first_part.str.contains(".", regex=False)
#     parts_split = first_part.str.split(".", n=1)

#     # เก็บชื่อสำหรับเปรียบเทียบในรูปแบบ "Last, First"
#     df["_corr_name"] = np.where(
#         has_semi & has_dot,
#         parts_split.str[1].str.strip() + ", " + parts_split.str[0].str.strip(),
#         None
#     )

#     # Helper function สำหรับการจัดการ List ข้อมูลที่แยกด้วยเครื่องหมาย Semi-colon
#     def split_col(col):
#         return df[col].fillna("").str.split(";").apply(
#             lambda x: [a.strip() for a in x if isinstance(a, str) and a.strip()]
#         )

#     # 2. เตรียมข้อมูล List สำหรับการ Explode
#     df["_authors_full"] = split_col("Author full names")
#     df["_authors_short"] = split_col("Authors")
#     df["_authors_with_aff"] = split_col("Authors with affiliations")

#     # 3. ขยาย Row (Explode) ให้ 1 แถวต่อ 1 ผู้เขียน
#     df_exp = df.explode("_authors_full").copy()
    
#     # สร้างลำดับผู้เขียน (0 = คนแรก)
#     df_exp["_author_order"] = df_exp.groupby(level=0).cumcount()

#     # 4. แยกชื่อและ ID ของผู้เขียน
#     af = df_exp["_authors_full"].fillna("").astype(str)
#     # ใช้ Regex ดึงชื่อและเลข ID ในวงเล็บ
#     extracted = af.str.extract(r"(.+?)\s*\((\d+)\)")
#     full_name_raw = extracted[0].fillna(af)
#     name_id = extracted[1]

#     # จัดการสลับชื่อ "นามสกุล, ชื่อ" ให้เป็น "ชื่อ นามสกุล"
#     has_comma = full_name_raw.str.contains(",", regex=False)
#     split_name = full_name_raw.str.split(",", n=1)
#     last_name = split_name.str[0].str.strip()
#     first_name = split_name.str[1].str.strip().fillna("")
    
#     df_exp["name"] = np.where(has_comma, first_name + " " + last_name, full_name_raw)
#     df_exp["name_id"] = name_id.values
#     df_exp["author_order"] = df_exp["_author_order"] + 1
#     df_exp["first_author"] = (df_exp["_author_order"] == 0).astype(int)

#     # 5. ดึงข้อมูล Profile (Affiliation) จาก "Authors with affiliations"
#     # ใช้เทคนิค split(",", 2) เพื่อข้าม นามสกุล และ ชื่อ แล้วดึงส่วนที่เหลือทั้งหมดเป็นสังกัด
#     orders = df_exp["_author_order"].tolist()
#     auth_affs = df_exp["_authors_with_aff"].tolist()
    
#     profiles = []
#     for i, raw_list in zip(orders, auth_affs):
#         if isinstance(raw_list, list) and i < len(raw_list):
#             entry = raw_list[i]
#             # แยกแค่ 2 คอมม่าแรก: [0]=Last, [1]=First, [2]=Affiliation
#             parts = entry.split(",", 2)
#             if len(parts) >= 3:
#                 profiles.append(parts[2].strip())
#             else:
#                 # กรณีฉุกเฉินถ้าไม่มีสังกัด ให้ดึงข้อมูลเท่าที่มี
#                 profiles.append(entry)
#         else:
#             profiles.append(None)
            
#     df_exp["profile"] = profiles

#     # 6. ตรวจสอบสถานะ Corresponding Author
#     cns = df_exp["_corr_name"].tolist()
#     shorts = df_exp["_authors_short"].tolist()

#     def check_corr(cn, sh_list, idx):
#         if not cn or not isinstance(cn, str):
#             return 0
#         if isinstance(sh_list, list) and idx < len(sh_list):
#             val = sh_list[idx]
#             if isinstance(val, str) and val:
#                 # ตรวจสอบการ Match แบบยืดหยุ่น (เผื่อกรณีมีช่องว่างหรือตัวย่อ)
#                 return 1 if (cn in val or val in cn) else 0
#         return 0

#     df_exp["corresponding"] = [
#         check_corr(cn, sh, i)
#         for cn, sh, i in zip(cns, shorts, orders)
#     ]
    
#     lookup = (
#         df_exp[df_exp["profile"].notna() & (df_exp["profile"] != "")]
#         .drop_duplicates(subset=["name_id"])
#         .set_index("name_id")["profile"]
#         .to_dict()
#     )
    
#     # Map ค่ากลับลงไปเฉพาะแถวที่ยังเป็น None หรือว่าง
#     def fill_profile(row):
#         if pd.isna(row["profile"]) or row["profile"] == "":
#             return lookup.get(row["name_id"], row["profile"])
#         return row["profile"]
    
#     df_exp["profile"] = df_exp.apply(fill_profile, axis=1)

#     # 7. เลือกคอลัมน์ที่ต้องการและคืนค่า
#     keep_columns = [
#         "EID", "name", "name_id", "profile", "author_order",
#         "first_author", "corresponding",
#         "Title", "Abstract", "Author Keywords", "Index Keywords", "Link"
#     ]

#     return df_exp[keep_columns].reset_index(drop=True)

# def build_ac_automaton(df_tax):
#     A = ahocorasick.Automaton()
#     for idx, kw in enumerate(df_tax["keyword_norm"].tolist()):
#         if kw:
#             A.add_word(f" {kw} ", (idx, kw))
#     A.make_automaton()
#     return A


# def map_eid_to_taxonomy(df_scopus, model, df_tax, tax_emb_matrix):
#     import time
#     device = "cuda" if torch.cuda.is_available() else "cpu"
#     model.to(device)

#     if isinstance(tax_emb_matrix, torch.Tensor):
#         tax_emb_matrix = tax_emb_matrix.to(device)

#     tax_rows_list = df_tax.to_dict("records")

#     print("Building Aho-Corasick automaton...")
#     A = build_ac_automaton(df_tax)

#     source_weights_map = {
#         "Author Keywords": 4.0,
#         "Index Keywords":  3.5,
#         "Title":           3.0,
#         "Abstract":        1.5,
#     }
#     sw_fields = list(source_weights_map.keys())
#     sw_vals   = list(source_weights_map.values())

#     df_papers = df_scopus.drop_duplicates(subset=["EID"]).reset_index(drop=True)
#     n_papers  = len(df_papers)

#     # ── vectorized text prep ──────────────────────────────────────────────────
#     print("Preparing paper texts...")
#     combined = (
#         df_papers["Title"].fillna("") + " " +
#         df_papers["Author Keywords"].fillna("") + " " +
#         df_papers["Index Keywords"].fillna("")
#     )
#     raw_texts  = normalize_series(combined).tolist()
#     texts_norm = [f" {t} " for t in raw_texts]

#     parts_df   = pd.DataFrame({k: normalize_series(df_papers[k].fillna(""))
#                                 for k in sw_fields})
#     parts_list = parts_df.to_dict("records")
#     eids       = df_papers["EID"].tolist()

#     # ── STEP A: AC matching ก่อน encode (เพื่อ encode เฉพาะ active papers) ───
#     print("Running AC matching (before encode)...")
#     t = time.time()
#     paper_tax_sw: list[dict[int, float]] = []

#     for row_i in tqdm(range(n_papers), desc="🔍 AC"):
#         parts            = parts_list[row_i]
#         text_norm_padded = texts_norm[row_i]

#         matched: dict[int, float] = {}
#         for _, (tax_idx, kw) in A.iter(text_norm_padded):
#             sw = max(
#                 (w for f, w in zip(sw_fields, sw_vals) if kw in parts[f]),
#                 default=0.0,
#             )
#             if sw > matched.get(tax_idx, 0.0):
#                 matched[tax_idx] = sw

#         paper_tax_sw.append(matched)

#     print(f"  AC done: {time.time()-t:.1f}s")

#     # ── STEP B: encode เฉพาะ active papers ───────────────────────────────────
#     active_mask   = [bool(m) for m in paper_tax_sw]
#     active_indices = [i for i, flag in enumerate(active_mask) if flag]
#     active_texts   = [raw_texts[i] for i in active_indices]

#     # ── OPTIMIZATION: ตัด text ให้สั้น (max 128 token ≈ 512 chars) ───────────
#     # Title+Keywords เพียงพอ ไม่ต้อง encode abstract ยาวๆ
#     MAX_CHARS = 400
#     active_texts_trimmed = [t[:MAX_CHARS] for t in active_texts]

#     n_active = len(active_indices)
#     print(f"  active papers: {n_active:,} / {n_papers:,}")
#     print(f"Encoding {n_active} active papers (trimmed to {MAX_CHARS} chars)...")

#     t = time.time()

#     # ── OPTIMIZATION: batch_size ใหญ่ขึ้นสำหรับ CPU, ใช้ num_workers ──────────
#     ENCODE_BATCH = 256 if device == "cpu" else 1024

#     active_embs = model.encode(
#         active_texts_trimmed,
#         batch_size=ENCODE_BATCH,
#         show_progress_bar=True,
#         convert_to_tensor=True,
#         device=device,
#         normalize_embeddings=True,
#     )  # [n_active, 384]
#     print(f"  encode done: {time.time()-t:.1f}s")

#     # map กลับ → full index
#     # สร้าง tensor เต็ม (zeros สำหรับ inactive — ไม่ถูกใช้งาน)
#     EMB_DIM = active_embs.shape[1]
#     paper_embs = torch.zeros(n_papers, EMB_DIM, device=device)
#     idx_tensor = torch.tensor(active_indices, dtype=torch.long, device=device)
#     paper_embs[idx_tensor] = active_embs

#     # ── STEP C: batched similarity (เหมือนเดิม แต่ใช้ active_indices แทน) ───
#     print("Computing similarities (chunked matmul)...")
#     t = time.time()

#     CHUNK   = 512
#     results = []

#     active = [(i, paper_tax_sw[i]) for i in active_indices]

#     for chunk_start in tqdm(range(0, len(active), CHUNK), desc="⚡ Sim"):
#         chunk = active[chunk_start: chunk_start + CHUNK]

#         all_tax_idx = sorted(set(ti for _, m in chunk for ti in m.keys()))
#         tax_idx_pos = {ti: pos for pos, ti in enumerate(all_tax_idx)}

#         p_idx  = [i for i, _ in chunk]
#         p_embs = paper_embs[p_idx]

#         tax_sub = tax_emb_matrix[all_tax_idx]
#         sim_mat = (p_embs @ tax_sub.T).cpu().numpy()

#         for local_i, (row_i, matched) in enumerate(chunk):
#             eid = eids[row_i]
#             for tax_idx, sw_val in matched.items():
#                 pos     = tax_idx_pos[tax_idx]
#                 sim_val = float(sim_mat[local_i, pos])
#                 if sim_val < 0.0:
#                     continue
#                 tr = tax_rows_list[tax_idx]
#                 results.append((
#                     eid,
#                     tr["taxonomy_id"], tr["l1_field"], tr["l2_domain"],
#                     tr["subfield_name"], tr["keyword"], tr["keyword_norm"],
#                     tr["keyword_type"], tr["keyword_rank_within_subfield"],
#                     tr["match_priority"], tr["keyword_weight"],
#                     sw_val, sim_val,
#                 ))

#     print(f"  sim done: {time.time()-t:.1f}s")

#     cols = [
#         "EID", "taxonomy_id", "l1_field", "l2_domain", "subfield_name",
#         "keyword", "keyword_norm", "keyword_type",
#         "keyword_rank_within_subfield", "match_priority", "keyword_weight",
#         "source_weight", "similarity",
#     ]
#     return pd.DataFrame(results, columns=cols)


# def merge_and_score(df_authors, df_eid_tax):
#     df = df_authors.merge(df_eid_tax, on="EID", how="inner")

#     kw_type_w = {
#         "exact_or_near_exact":       1.2,
#         "token_or_phrase_expansion": 1.0,
#         "domain_seed":               0.8,
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
#         default=0.2,
#     )
#     df["expertise_score"] = df["paper_topic_score"] * role_w

#     # ── OPTIMIZATION: groupby ด้วย observed=True + sort=False ────────────────
#     df_final = df.groupby(
#         [
#             "name_id",
#             "name",
#             "taxonomy_id",
#             "l1_field",
#             "l2_domain",
#             "subfield_name"
#         ],
#         sort=False,
#         observed=True,
#     ).agg(
#         expertise_score      = ("expertise_score", "sum"),
#         paper_count          = ("EID", "nunique"),
#         first_author_papers  = ("first_author", "sum"),
#         corresponding_papers = ("corresponding", "sum"),
#         author_papers        = ("EID", "count"),
#         avg_similarity       = ("similarity", "mean"),

#         evidence_paper_ids   = (
#             "EID",
#             lambda x: x.unique().tolist()
#         ),

#         evidence_titles      = (
#             "Title",
#             lambda x: x.unique().tolist()
#         ),

#         evidence_links       = (
#             "Link",
#             lambda x: x.unique().tolist()
#         ),

#         profile              = ("profile", "first"),

#     ).reset_index().rename(
#         columns={
#             "name_id": "author_id",
#             "name": "author_name"
#         }
#     )

#     return df_final


# def mapping_hybrid(df_scopus, model, df_tax, tax_emb_matrix):
#     import time
#     t0 = time.time()

#     print("=" * 50)
#     print("Step 1: map EID → taxonomy")
#     df_eid_tax = map_eid_to_taxonomy(df_scopus, model, df_tax, tax_emb_matrix)
#     t1 = time.time()
#     print(f"✅ Step 1: {t1-t0:.1f}s | {len(df_eid_tax):,} rows\n")

#     print("Step 2: process scopus authors")
#     df_authors = process_scopus_authors(df_scopus)
#     t2 = time.time()
#     print(f"✅ Step 2: {t2-t1:.1f}s | {len(df_authors):,} rows\n")

#     print("Step 3: merge + score")
#     df_final = merge_and_score(df_authors, df_eid_tax)
#     t3 = time.time()
#     print(f"✅ Step 3: {t3-t2:.1f}s | {len(df_final):,} rows\n")

#     df_final["_epids_key"] = df_final["evidence_paper_ids"].apply(tuple)

#     df_top3 = (
#         df_final
#         .drop_duplicates(subset=["author_id", "taxonomy_id", "_epids_key"])
#         .sort_values("expertise_score", ascending=False)
#         .groupby(["author_id", "_epids_key"], sort=False)
#         .head(3)
#         .drop(columns=["_epids_key"])
#         .sort_values("taxonomy_id", ascending=True)
#         .reset_index(drop=True)
#     )

#     print(f"🏁 Total: {time.time()-t0:.1f}s | {len(df_top3):,} rows")
#     return df_top3


from sentence_transformers import SentenceTransformer
import torch
import numpy as np
import pandas as pd
import re
from tqdm import tqdm
import ahocorasick

# ── compile regex ครั้งเดียว ──────────────────────────────────────────────────
_RE_CLEAN  = re.compile(r"[^a-z0-9\s\-_]")
_RE_SPACE  = re.compile(r"\s+")

def normalize_text(text):
    if pd.isna(text):
        return ""
    text = str(text).lower()
    text = _RE_CLEAN.sub(" ", text)
    text = _RE_SPACE.sub(" ", text).strip()
    return text

def normalize_series(s: pd.Series) -> pd.Series:
    return (
        s.fillna("")
         .str.lower()
         .str.replace(_RE_CLEAN, " ", regex=True)
         .str.replace(_RE_SPACE, " ", regex=True)
         .str.strip()
    )

def process_scopus_authors(df):
    # ป้องกันการแก้ไขข้อมูลใน DataFrame ต้นฉบับ
    df = df.copy()

    # 1. จัดการข้อมูล Correspondence Address เพื่อหาตัวผู้เขียนหลัก (Corresponding Author)
    corr = df["Correspondence Address"].fillna("")
    has_semi = corr.str.contains(";", regex=False)
    first_part = corr.str.split(";").str[0].str.strip()
    has_dot = first_part.str.contains(".", regex=False)
    parts_split = first_part.str.split(".", n=1)

    # เก็บชื่อสำหรับเปรียบเทียบในรูปแบบ "Last, First"
    df["_corr_name"] = np.where(
        has_semi & has_dot,
        parts_split.str[1].str.strip() + ", " + parts_split.str[0].str.strip(),
        None
    )

    # Helper function สำหรับการจัดการ List ข้อมูลที่แยกด้วยเครื่องหมาย Semi-colon
    def split_col(col):
        return df[col].fillna("").str.split(";").apply(
            lambda x: [a.strip() for a in x if isinstance(a, str) and a.strip()]
        )

    # 2. เตรียมข้อมูล List สำหรับการ Explode
    df["_authors_full"] = split_col("Author full names")
    df["_authors_short"] = split_col("Authors")
    df["_authors_with_aff"] = split_col("Authors with affiliations")

    # 3. ขยาย Row (Explode) ให้ 1 แถวต่อ 1 ผู้เขียน
    df_exp = df.explode("_authors_full").copy()
    
    # สร้างลำดับผู้เขียน (0 = คนแรก)
    df_exp["_author_order"] = df_exp.groupby(level=0).cumcount()

    # 4. แยกชื่อและ ID ของผู้เขียน
    af = df_exp["_authors_full"].fillna("").astype(str)
    # ใช้ Regex ดึงชื่อและเลข ID ในวงเล็บ
    extracted = af.str.extract(r"(.+?)\s*\((\d+)\)")
    full_name_raw = extracted[0].fillna(af)
    name_id = extracted[1]

    # จัดการสลับชื่อ "นามสกุล, ชื่อ" ให้เป็น "ชื่อ นามสกุล"
    has_comma = full_name_raw.str.contains(",", regex=False)
    split_name = full_name_raw.str.split(",", n=1)
    last_name = split_name.str[0].str.strip()
    first_name = split_name.str[1].str.strip().fillna("")
    
    df_exp["name"] = np.where(has_comma, first_name + " " + last_name, full_name_raw)
    df_exp["name_id"] = name_id.values
    df_exp["author_order"] = df_exp["_author_order"] + 1
    df_exp["first_author"] = (df_exp["_author_order"] == 0).astype(int)

    # 5. ดึงข้อมูล Profile (Affiliation) จาก "Authors with affiliations"
    # ใช้เทคนิค split(",", 2) เพื่อข้าม นามสกุล และ ชื่อ แล้วดึงส่วนที่เหลือทั้งหมดเป็นสังกัด
    orders = df_exp["_author_order"].tolist()
    auth_affs = df_exp["_authors_with_aff"].tolist()
    
    profiles = []
    for i, raw_list in zip(orders, auth_affs):
        if isinstance(raw_list, list) and i < len(raw_list):
            entry = raw_list[i]
            # แยกแค่ 2 คอมม่าแรก: [0]=Last, [1]=First, [2]=Affiliation
            parts = entry.split(",", 2)
            if len(parts) >= 3:
                profiles.append(parts[2].strip())
            else:
                # กรณีฉุกเฉินถ้าไม่มีสังกัด ให้ดึงข้อมูลเท่าที่มี
                profiles.append(entry)
        else:
            profiles.append(None)
            
    df_exp["profile"] = profiles

    # 6. ตรวจสอบสถานะ Corresponding Author
    cns = df_exp["_corr_name"].tolist()
    shorts = df_exp["_authors_short"].tolist()

    def check_corr(cn, sh_list, idx):
        if not cn or not isinstance(cn, str):
            return 0
        if isinstance(sh_list, list) and idx < len(sh_list):
            val = sh_list[idx]
            if isinstance(val, str) and val:
                # ตรวจสอบการ Match แบบยืดหยุ่น (เผื่อกรณีมีช่องว่างหรือตัวย่อ)
                return 1 if (cn in val or val in cn) else 0
        return 0

    df_exp["corresponding"] = [
        check_corr(cn, sh, i)
        for cn, sh, i in zip(cns, shorts, orders)
    ]
    
    lookup = (
        df_exp[df_exp["profile"].notna() & (df_exp["profile"] != "")]
        .drop_duplicates(subset=["name_id"])
        .set_index("name_id")["profile"]
        .to_dict()
    )
    
    # Map ค่ากลับลงไปเฉพาะแถวที่ยังเป็น None หรือว่าง
    def fill_profile(row):
        if pd.isna(row["profile"]) or row["profile"] == "":
            return lookup.get(row["name_id"], row["profile"])
        return row["profile"]
    
    df_exp["profile"] = df_exp.apply(fill_profile, axis=1)

    # 7. เลือกคอลัมน์ที่ต้องการและคืนค่า
    keep_columns = [
        "EID", "name", "name_id", "profile", "author_order",
        "first_author", "corresponding",
        "Title", "Abstract", "Author Keywords", "Index Keywords", "Link"
    ]

    return df_exp[keep_columns].reset_index(drop=True)

def build_ac_automaton(df_tax):
    A = ahocorasick.Automaton()
    for idx, kw in enumerate(df_tax["keyword_norm"].tolist()):
        if kw:
            A.add_word(f" {kw} ", (idx, kw))
    A.make_automaton()
    return A


def map_eid_to_taxonomy(df_scopus, model, df_tax, tax_emb_matrix):
    import time
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)

    if isinstance(tax_emb_matrix, torch.Tensor):
        tax_emb_matrix = tax_emb_matrix.to(device)

    tax_rows_list = df_tax.to_dict("records")

    print("Building Aho-Corasick automaton...")
    A = build_ac_automaton(df_tax)

    source_weights_map = {
        "Author Keywords": 4.0,
        "Index Keywords":  3.5,
        "Title":           3.0,
        "Abstract":        1.5,
    }
    sw_fields = list(source_weights_map.keys())
    sw_vals   = list(source_weights_map.values())

    df_papers = df_scopus.drop_duplicates(subset=["EID"]).reset_index(drop=True)
    n_papers  = len(df_papers)

    # ── vectorized text prep ──────────────────────────────────────────────────
    print("Preparing paper texts...")
    combined = (
        df_papers["Title"].fillna("") + " " +
        df_papers["Author Keywords"].fillna("") + " " +
        df_papers["Index Keywords"].fillna("")
    )
    raw_texts  = normalize_series(combined).tolist()
    texts_norm = [f" {t} " for t in raw_texts]

    parts_df   = pd.DataFrame({k: normalize_series(df_papers[k].fillna(""))
                                for k in sw_fields})
    parts_list = parts_df.to_dict("records")
    eids       = df_papers["EID"].tolist()

    # ── STEP A: AC matching ก่อน encode (เพื่อ encode เฉพาะ active papers) ───
    print("Running AC matching (before encode)...")
    t = time.time()
    paper_tax_sw: list[dict[int, float]] = []

    for row_i in tqdm(range(n_papers), desc="🔍 AC"):
        parts            = parts_list[row_i]
        text_norm_padded = texts_norm[row_i]

        matched: dict[int, float] = {}
        for _, (tax_idx, kw) in A.iter(text_norm_padded):
            sw = max(
                (w for f, w in zip(sw_fields, sw_vals) if kw in parts[f]),
                default=0.0,
            )
            if sw > matched.get(tax_idx, 0.0):
                matched[tax_idx] = sw

        paper_tax_sw.append(matched)

    print(f"  AC done: {time.time()-t:.1f}s")

    # ── STEP B: encode เฉพาะ active papers ───────────────────────────────────
    active_mask   = [bool(m) for m in paper_tax_sw]
    active_indices = [i for i, flag in enumerate(active_mask) if flag]
    active_texts   = [raw_texts[i] for i in active_indices]

    # ── OPTIMIZATION: ตัด text ให้สั้น (max 128 token ≈ 512 chars) ───────────
    # Title+Keywords เพียงพอ ไม่ต้อง encode abstract ยาวๆ
    MAX_CHARS = 400
    active_texts_trimmed = [t[:MAX_CHARS] for t in active_texts]

    n_active = len(active_indices)
    print(f"  active papers: {n_active:,} / {n_papers:,}")
    print(f"Encoding {n_active} active papers (trimmed to {MAX_CHARS} chars)...")

    t = time.time()

    # ── OPTIMIZATION: batch_size ใหญ่ขึ้นสำหรับ CPU, ใช้ num_workers ──────────
    ENCODE_BATCH = 256 if device == "cpu" else 1024

    active_embs = model.encode(
        active_texts_trimmed,
        batch_size=ENCODE_BATCH,
        show_progress_bar=True,
        convert_to_tensor=True,
        device=device,
        normalize_embeddings=True,
    )  # [n_active, 384]
    print(f"  encode done: {time.time()-t:.1f}s")

    # map กลับ → full index
    # สร้าง tensor เต็ม (zeros สำหรับ inactive — ไม่ถูกใช้งาน)
    EMB_DIM = active_embs.shape[1]
    paper_embs = torch.zeros(n_papers, EMB_DIM, device=device)
    idx_tensor = torch.tensor(active_indices, dtype=torch.long, device=device)
    paper_embs[idx_tensor] = active_embs

    # ── STEP C: batched similarity (เหมือนเดิม แต่ใช้ active_indices แทน) ───
    print("Computing similarities (chunked matmul)...")
    t = time.time()

    CHUNK   = 512
    results = []

    active = [(i, paper_tax_sw[i]) for i in active_indices]

    for chunk_start in tqdm(range(0, len(active), CHUNK), desc="⚡ Sim"):
        chunk = active[chunk_start: chunk_start + CHUNK]

        all_tax_idx = sorted(set(ti for _, m in chunk for ti in m.keys()))
        tax_idx_pos = {ti: pos for pos, ti in enumerate(all_tax_idx)}

        p_idx  = [i for i, _ in chunk]
        p_embs = paper_embs[p_idx]

        tax_sub = tax_emb_matrix[all_tax_idx]
        sim_mat = (p_embs @ tax_sub.T).cpu().numpy()

        for local_i, (row_i, matched) in enumerate(chunk):
            eid = eids[row_i]
            for tax_idx, sw_val in matched.items():
                pos     = tax_idx_pos[tax_idx]
                sim_val = float(sim_mat[local_i, pos])
                if sim_val < 0.0:
                    continue
                tr = tax_rows_list[tax_idx]
                results.append((
                    eid,
                    tr["taxonomy_id"], tr["l1_field"], tr["l2_domain"],
                    tr["subfield_name"], tr["keyword"], tr["keyword_norm"],
                    tr["keyword_type"], tr["keyword_rank_within_subfield"],
                    tr["match_priority"], tr["keyword_weight"],
                    sw_val, sim_val,
                ))

    print(f"  sim done: {time.time()-t:.1f}s")

    cols = [
        "EID", "taxonomy_id", "l1_field", "l2_domain", "subfield_name",
        "keyword", "keyword_norm", "keyword_type",
        "keyword_rank_within_subfield", "match_priority", "keyword_weight",
        "source_weight", "similarity",
    ]
    return pd.DataFrame(results, columns=cols)


def merge_and_score(df_authors, df_eid_tax):
    df = df_authors.merge(df_eid_tax, on="EID", how="inner")

    kw_type_w = {
        "exact_or_near_exact":       1.2,
        "token_or_phrase_expansion": 1.0,
        "domain_seed":               0.8,
    }

    df["paper_topic_score"] = (
        df["keyword_weight"] *
        df["match_priority"] *
        df["keyword_type"].map(kw_type_w).fillna(0.7) *
        df["source_weight"]
    )

    role_w = np.select(
        [df["first_author"] == 1, df["corresponding"] == 1],
        [1.0, 0.7],
        default=0.2,
    )
    df["expertise_score"] = df["paper_topic_score"] * role_w

    # ── OPTIMIZATION: groupby ด้วย observed=True + sort=False ────────────────
    df_final = df.groupby(
        [
            "name_id",
            "name",
            "taxonomy_id",
            "l1_field",
            "l2_domain",
            "subfield_name"
        ],
        sort=False,
        observed=True,
    ).agg(
        expertise_score      = ("expertise_score", "sum"),
        paper_count          = ("EID", "nunique"),
        first_author_papers  = ("first_author", "sum"),
        corresponding_papers = ("corresponding", "sum"),
        author_papers        = ("EID", "count"),
        avg_similarity       = ("similarity", "mean"),

        evidence_paper_ids   = (
            "EID",
            lambda x: x.unique().tolist()
        ),

        evidence_titles      = (
            "Title",
            lambda x: x.unique().tolist()
        ),

        evidence_links       = (
            "Link",
            lambda x: x.unique().tolist()
        ),

        profile              = ("profile", "first"),

    ).reset_index().rename(
        columns={
            "name_id":        "author_id",
            "name":           "author_name",
            "evidence_links": "link",          # ← rename ที่นี่เลย ให้ df_final มี link
        }
    )

    return df_final


def mapping_hybrid(df_scopus, model, df_tax, tax_emb_matrix):
    import time
    t0 = time.time()

    print("=" * 50)
    print("Step 1: map EID → taxonomy")
    df_eid_tax = map_eid_to_taxonomy(df_scopus, model, df_tax, tax_emb_matrix)
    t1 = time.time()
    print(f"✅ Step 1: {t1-t0:.1f}s | {len(df_eid_tax):,} rows\n")

    print("Step 2: process scopus authors")
    df_authors = process_scopus_authors(df_scopus)
    t2 = time.time()
    print(f"✅ Step 2: {t2-t1:.1f}s | {len(df_authors):,} rows\n")

    print("Step 3: merge + score")
    df_final = merge_and_score(df_authors, df_eid_tax)
    t3 = time.time()
    print(f"✅ Step 3: {t3-t2:.1f}s | {len(df_final):,} rows\n")

    df_final["_epids_key"] = df_final["evidence_paper_ids"].apply(tuple)

    df_top3 = (
        df_final
        .drop_duplicates(subset=["author_id", "taxonomy_id", "_epids_key"])
        .sort_values("expertise_score", ascending=False)
        .groupby(["author_id", "_epids_key"], sort=False)
        .head(3)
        .drop(columns=["_epids_key"])
        .sort_values("taxonomy_id", ascending=True)
        .reset_index(drop=True)
    )

    print(f"🏁 Total: {time.time()-t0:.1f}s | {len(df_top3):,} rows")
    return df_top3










# from sentence_transformers import SentenceTransformer
# import torch
# import numpy as np
# import pandas as pd
# import re
# from tqdm import tqdm
# import ahocorasick

# # ── compile regex ครั้งเดียว ──────────────────────────────────────────────────
# _RE_CLEAN  = re.compile(r"[^a-z0-9\s\-_]")
# _RE_SPACE  = re.compile(r"\s+")

# def normalize_text(text):
#     if pd.isna(text):
#         return ""
#     text = str(text).lower()
#     text = _RE_CLEAN.sub(" ", text)
#     text = _RE_SPACE.sub(" ", text).strip()
#     return text

# def normalize_series(s: pd.Series) -> pd.Series:
#     return (
#         s.fillna("")
#          .str.lower()
#          .str.replace(_RE_CLEAN, " ", regex=True)
#          .str.replace(_RE_SPACE, " ", regex=True)
#          .str.strip()
#     )

# def process_scopus_authors(df):
#     # ป้องกันการแก้ไขข้อมูลใน DataFrame ต้นฉบับ
#     df = df.copy()

#     # 1. จัดการข้อมูล Correspondence Address เพื่อหาตัวผู้เขียนหลัก (Corresponding Author)
#     corr = df["Correspondence Address"].fillna("")
#     has_semi = corr.str.contains(";", regex=False)
#     first_part = corr.str.split(";").str[0].str.strip()
#     has_dot = first_part.str.contains(".", regex=False)
#     parts_split = first_part.str.split(".", n=1)

#     # เก็บชื่อสำหรับเปรียบเทียบในรูปแบบ "Last, First"
#     df["_corr_name"] = np.where(
#         has_semi & has_dot,
#         parts_split.str[1].str.strip() + ", " + parts_split.str[0].str.strip(),
#         None
#     )

#     # Helper function สำหรับการจัดการ List ข้อมูลที่แยกด้วยเครื่องหมาย Semi-colon
#     def split_col(col):
#         return df[col].fillna("").str.split(";").apply(
#             lambda x: [a.strip() for a in x if isinstance(a, str) and a.strip()]
#         )

#     # 2. เตรียมข้อมูล List สำหรับการ Explode
#     df["_authors_full"] = split_col("Author full names")
#     df["_authors_short"] = split_col("Authors")
#     df["_authors_with_aff"] = split_col("Authors with affiliations")

#     # 3. ขยาย Row (Explode) ให้ 1 แถวต่อ 1 ผู้เขียน
#     df_exp = df.explode("_authors_full").copy()
    
#     # สร้างลำดับผู้เขียน (0 = คนแรก)
#     df_exp["_author_order"] = df_exp.groupby(level=0).cumcount()

#     # 4. แยกชื่อและ ID ของผู้เขียน
#     af = df_exp["_authors_full"].fillna("").astype(str)
#     # ใช้ Regex ดึงชื่อและเลข ID ในวงเล็บ
#     extracted = af.str.extract(r"(.+?)\s*\((\d+)\)")
#     full_name_raw = extracted[0].fillna(af)
#     name_id = extracted[1]

#     # จัดการสลับชื่อ "นามสกุล, ชื่อ" ให้เป็น "ชื่อ นามสกุล"
#     has_comma = full_name_raw.str.contains(",", regex=False)
#     split_name = full_name_raw.str.split(",", n=1)
#     last_name = split_name.str[0].str.strip()
#     first_name = split_name.str[1].str.strip().fillna("")
    
#     df_exp["name"] = np.where(has_comma, first_name + " " + last_name, full_name_raw)
#     df_exp["name_id"] = name_id.values
#     df_exp["author_order"] = df_exp["_author_order"] + 1
#     df_exp["first_author"] = (df_exp["_author_order"] == 0).astype(int)

#     # 5. ดึงข้อมูล Profile (Affiliation) จาก "Authors with affiliations"
#     # ใช้เทคนิค split(",", 2) เพื่อข้าม นามสกุล และ ชื่อ แล้วดึงส่วนที่เหลือทั้งหมดเป็นสังกัด
#     orders = df_exp["_author_order"].tolist()
#     auth_affs = df_exp["_authors_with_aff"].tolist()
    
#     profiles = []
#     for i, raw_list in zip(orders, auth_affs):
#         if isinstance(raw_list, list) and i < len(raw_list):
#             entry = raw_list[i]
#             # แยกแค่ 2 คอมม่าแรก: [0]=Last, [1]=First, [2]=Affiliation
#             parts = entry.split(",", 2)
#             if len(parts) >= 3:
#                 profiles.append(parts[2].strip())
#             else:
#                 # กรณีฉุกเฉินถ้าไม่มีสังกัด ให้ดึงข้อมูลเท่าที่มี
#                 profiles.append(entry)
#         else:
#             profiles.append(None)
            
#     df_exp["profile"] = profiles

#     # 6. ตรวจสอบสถานะ Corresponding Author
#     cns = df_exp["_corr_name"].tolist()
#     shorts = df_exp["_authors_short"].tolist()

#     def check_corr(cn, sh_list, idx):
#         if not cn or not isinstance(cn, str):
#             return 0
#         if isinstance(sh_list, list) and idx < len(sh_list):
#             val = sh_list[idx]
#             if isinstance(val, str) and val:
#                 # ตรวจสอบการ Match แบบยืดหยุ่น (เผื่อกรณีมีช่องว่างหรือตัวย่อ)
#                 return 1 if (cn in val or val in cn) else 0
#         return 0

#     df_exp["corresponding"] = [
#         check_corr(cn, sh, i)
#         for cn, sh, i in zip(cns, shorts, orders)
#     ]
    
#     lookup = (
#         df_exp[df_exp["profile"].notna() & (df_exp["profile"] != "")]
#         .drop_duplicates(subset=["name_id"])
#         .set_index("name_id")["profile"]
#         .to_dict()
#     )
    
#     # Map ค่ากลับลงไปเฉพาะแถวที่ยังเป็น None หรือว่าง
#     def fill_profile(row):
#         if pd.isna(row["profile"]) or row["profile"] == "":
#             return lookup.get(row["name_id"], row["profile"])
#         return row["profile"]
    
#     df_exp["profile"] = df_exp.apply(fill_profile, axis=1)

#     # 7. เลือกคอลัมน์ที่ต้องการและคืนค่า
#     keep_columns = [
#         "EID", "name", "name_id", "profile", "author_order",
#         "first_author", "corresponding",
#         "Title", "Abstract", "Author Keywords", "Index Keywords"
#     ]

#     return df_exp[keep_columns].reset_index(drop=True)

# def build_ac_automaton(df_tax):
#     A = ahocorasick.Automaton()
#     for idx, kw in enumerate(df_tax["keyword_norm"].tolist()):
#         if kw:
#             A.add_word(f" {kw} ", (idx, kw))
#     A.make_automaton()
#     return A


# def map_eid_to_taxonomy(df_scopus, model, df_tax, tax_emb_matrix):
#     import time
#     device = "cuda" if torch.cuda.is_available() else "cpu"
#     model.to(device)

#     if isinstance(tax_emb_matrix, torch.Tensor):
#         tax_emb_matrix = tax_emb_matrix.to(device)

#     tax_rows_list = df_tax.to_dict("records")

#     print("Building Aho-Corasick automaton...")
#     A = build_ac_automaton(df_tax)

#     source_weights_map = {
#         "Author Keywords": 4.0,
#         "Index Keywords":  3.5,
#         "Title":           3.0,
#         "Abstract":        1.5,
#     }
#     sw_fields = list(source_weights_map.keys())
#     sw_vals   = list(source_weights_map.values())

#     df_papers = df_scopus.drop_duplicates(subset=["EID"]).reset_index(drop=True)
#     n_papers  = len(df_papers)

#     # ── vectorized text prep ──────────────────────────────────────────────────
#     print("Preparing paper texts...")
#     combined = (
#         df_papers["Title"].fillna("") + " " +
#         df_papers["Author Keywords"].fillna("") + " " +
#         df_papers["Index Keywords"].fillna("")
#     )
#     raw_texts  = normalize_series(combined).tolist()
#     texts_norm = [f" {t} " for t in raw_texts]

#     parts_df   = pd.DataFrame({k: normalize_series(df_papers[k].fillna(""))
#                                 for k in sw_fields})
#     parts_list = parts_df.to_dict("records")
#     eids       = df_papers["EID"].tolist()

#     # ── STEP A: AC matching ก่อน encode (เพื่อ encode เฉพาะ active papers) ───
#     print("Running AC matching (before encode)...")
#     t = time.time()
#     paper_tax_sw: list[dict[int, float]] = []

#     for row_i in tqdm(range(n_papers), desc="🔍 AC"):
#         parts            = parts_list[row_i]
#         text_norm_padded = texts_norm[row_i]

#         matched: dict[int, float] = {}
#         for _, (tax_idx, kw) in A.iter(text_norm_padded):
#             sw = max(
#                 (w for f, w in zip(sw_fields, sw_vals) if kw in parts[f]),
#                 default=0.0,
#             )
#             if sw > matched.get(tax_idx, 0.0):
#                 matched[tax_idx] = sw

#         paper_tax_sw.append(matched)

#     print(f"  AC done: {time.time()-t:.1f}s")

#     # ── STEP B: encode เฉพาะ active papers ───────────────────────────────────
#     active_mask   = [bool(m) for m in paper_tax_sw]
#     active_indices = [i for i, flag in enumerate(active_mask) if flag]
#     active_texts   = [raw_texts[i] for i in active_indices]

#     # ── OPTIMIZATION: ตัด text ให้สั้น (max 128 token ≈ 512 chars) ───────────
#     # Title+Keywords เพียงพอ ไม่ต้อง encode abstract ยาวๆ
#     MAX_CHARS = 400
#     active_texts_trimmed = [t[:MAX_CHARS] for t in active_texts]

#     n_active = len(active_indices)
#     print(f"  active papers: {n_active:,} / {n_papers:,}")
#     print(f"Encoding {n_active} active papers (trimmed to {MAX_CHARS} chars)...")

#     t = time.time()

#     # ── OPTIMIZATION: batch_size ใหญ่ขึ้นสำหรับ CPU, ใช้ num_workers ──────────
#     ENCODE_BATCH = 256 if device == "cpu" else 1024

#     active_embs = model.encode(
#         active_texts_trimmed,
#         batch_size=ENCODE_BATCH,
#         show_progress_bar=True,
#         convert_to_tensor=True,
#         device=device,
#         normalize_embeddings=True,
#     )  # [n_active, 384]
#     print(f"  encode done: {time.time()-t:.1f}s")

#     # map กลับ → full index
#     # สร้าง tensor เต็ม (zeros สำหรับ inactive — ไม่ถูกใช้งาน)
#     EMB_DIM = active_embs.shape[1]
#     paper_embs = torch.zeros(n_papers, EMB_DIM, device=device)
#     idx_tensor = torch.tensor(active_indices, dtype=torch.long, device=device)
#     paper_embs[idx_tensor] = active_embs

#     # ── STEP C: batched similarity (เหมือนเดิม แต่ใช้ active_indices แทน) ───
#     print("Computing similarities (chunked matmul)...")
#     t = time.time()

#     CHUNK   = 512
#     results = []

#     active = [(i, paper_tax_sw[i]) for i in active_indices]

#     for chunk_start in tqdm(range(0, len(active), CHUNK), desc="⚡ Sim"):
#         chunk = active[chunk_start: chunk_start + CHUNK]

#         all_tax_idx = sorted(set(ti for _, m in chunk for ti in m.keys()))
#         tax_idx_pos = {ti: pos for pos, ti in enumerate(all_tax_idx)}

#         p_idx  = [i for i, _ in chunk]
#         p_embs = paper_embs[p_idx]

#         tax_sub = tax_emb_matrix[all_tax_idx]
#         sim_mat = (p_embs @ tax_sub.T).cpu().numpy()

#         for local_i, (row_i, matched) in enumerate(chunk):
#             eid = eids[row_i]
#             for tax_idx, sw_val in matched.items():
#                 pos     = tax_idx_pos[tax_idx]
#                 sim_val = float(sim_mat[local_i, pos])
#                 if sim_val < 0.0:
#                     continue
#                 tr = tax_rows_list[tax_idx]
#                 results.append((
#                     eid,
#                     tr["taxonomy_id"], tr["l1_field"], tr["l2_domain"],
#                     tr["subfield_name"], tr["keyword"], tr["keyword_norm"],
#                     tr["keyword_type"], tr["keyword_rank_within_subfield"],
#                     tr["match_priority"], tr["keyword_weight"],
#                     sw_val, sim_val,
#                 ))

#     print(f"  sim done: {time.time()-t:.1f}s")

#     cols = [
#         "EID", "taxonomy_id", "l1_field", "l2_domain", "subfield_name",
#         "keyword", "keyword_norm", "keyword_type",
#         "keyword_rank_within_subfield", "match_priority", "keyword_weight",
#         "source_weight", "similarity",
#     ]
#     return pd.DataFrame(results, columns=cols)


# def merge_and_score(df_authors, df_eid_tax):
#     df = df_authors.merge(df_eid_tax, on="EID", how="inner")

#     kw_type_w = {
#         "exact_or_near_exact":       1.2,
#         "token_or_phrase_expansion": 1.0,
#         "domain_seed":               0.8,
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
#         default=0.2,
#     )
#     df["expertise_score"] = df["paper_topic_score"] * role_w

#     # ── OPTIMIZATION: groupby ด้วย observed=True + sort=False ────────────────
#     df_final = df.groupby(
#         ["name_id", "name", "taxonomy_id", "l1_field", "l2_domain", "subfield_name"],
#         sort=False,
#         observed=True,
#     ).agg(
#         expertise_score      = ("expertise_score", "sum"),
#         paper_count          = ("EID", "nunique"),
#         first_author_papers  = ("first_author", "sum"),
#         corresponding_papers = ("corresponding", "sum"),
#         author_papers        = ("EID", "count"),
#         avg_similarity       = ("similarity", "mean"),
#         evidence_paper_ids   = ("EID",   lambda x: list(set(x))),
#         evidence_titles      = ("Title", lambda x: list(set(x))),
#         profile              = ("profile", "first"),
#     ).reset_index().rename(columns={"name_id": "author_id", "name": "author_name"})

#     return df_final


# def mapping_hybrid(df_scopus, model, df_tax, tax_emb_matrix):
#     import time
#     t0 = time.time()

#     print("=" * 50)
#     print("Step 1: map EID → taxonomy")
#     df_eid_tax = map_eid_to_taxonomy(df_scopus, model, df_tax, tax_emb_matrix)
#     t1 = time.time()
#     print(f"✅ Step 1: {t1-t0:.1f}s | {len(df_eid_tax):,} rows\n")

#     print("Step 2: process scopus authors")
#     df_authors = process_scopus_authors(df_scopus)
#     t2 = time.time()
#     print(f"✅ Step 2: {t2-t1:.1f}s | {len(df_authors):,} rows\n")

#     print("Step 3: merge + score")
#     df_final = merge_and_score(df_authors, df_eid_tax)
#     t3 = time.time()
#     print(f"✅ Step 3: {t3-t2:.1f}s | {len(df_final):,} rows\n")

#     df_final["_epids_key"] = df_final["evidence_paper_ids"].apply(tuple)

#     df_top3 = (
#         df_final
#         .drop_duplicates(subset=["author_id", "taxonomy_id", "_epids_key"])
#         .sort_values("expertise_score", ascending=False)
#         .groupby(["author_id", "_epids_key"], sort=False)
#         .head(3)
#         .drop(columns=["_epids_key"])
#         .sort_values("taxonomy_id", ascending=True)
#         .reset_index(drop=True)
#     )

#     print(f"🏁 Total: {time.time()-t0:.1f}s | {len(df_top3):,} rows")
#     return df_top3




