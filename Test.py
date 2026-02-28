import pandas as pd

def identify_corresponding(row):
    if not row['Journal']:
        return ""

    name = str(row['author_list']).lower()
    address = str(row.get('Correspondence Address', '')).lower()

    if name != 'nan' and name in address:
        return "Corresponding Author"

    return ""

def format_author_name(fullname, author_id):
    """
    แปลง 'LastName, FirstName' -> 'FirstName LastName (ID)'
    และรองรับกรณีชื่อไม่มี comma
    """
    if pd.isna(fullname):
        return None

    name = str(fullname).strip()

    # กรณีมี comma (Scopus format)
    if ',' in name:
        last, first = [n.strip() for n in name.split(',', 1)]
        formatted = f"{first} {last}"
    else:
        # กรณี format แปลก ๆ ให้ใช้เดิม
        formatted = name

    return f"{formatted} ({author_id})"

def test_ingest(dataMain):
    dataTest = pd.DataFrame(dataMain)
    # 1. แยก Author ออกเป็นรายบุคคล (ใช้ ";" เป็นตัวแบ่งตามรูปแบบ Scopus)
    dataTest['author_list'] = dataTest['Authors'].str.split(';')
    # กระจายแถว (Explode) ให้ 1 แถวต่อผู้เขียน 1 คน
    dataTest= dataTest.explode('author_list').reset_index(drop=True)
    dataTest['author_list'] = dataTest['author_list'].str.strip()

    # 2. ทำ Ordering และกำหนดบทบาท (Roles)
    # สร้างคอลัมน์ลำดับที่ 1, 2, 3... ภายในบทความเดียวกัน (EID)
    dataTest['author_order'] = dataTest.groupby('EID').cumcount() + 1

    # ระบุ First Author (คนที่ 1)
    dataTest['first_author'] = dataTest['author_order'].apply(
        lambda x: "First Author" if x == 1 else ""
    )
    # --- ทำความสะอาด Source title ก่อน ---
    dataTest['Source title_clean'] = (
        dataTest['Source title']
        .astype(str)                          # บังคับเป็น string
        .str.replace('\xa0', ' ', regex=False) # ลบ hidden space จาก Scopus
        .str.strip()                           # ตัดช่องว่างหัวท้าย
        .str.lower()                           # ทำเป็น lowercase เพื่อ match ง่าย
    )

    # --- ตรวจคำว่า journal ---
    dataTest['Journal'] = dataTest['Source title_clean'].apply(
        lambda x: "corresponding" if "journal" in x else ""
    )

    dataTest['corresponding'] = dataTest.apply(
        identify_corresponding, axis=1
    )

    return dataTest

exported_functions = {
    "test_ingest": test_ingest,
    "format_author_name": format_author_name
}

