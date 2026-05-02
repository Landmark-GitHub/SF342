import asyncio
import json
from google import genai
import pandas as pd

def format_author_name(dataMain):
    # ---------------------------------
    # 0. สร้าง DataFrame
    # ---------------------------------
    dataTest = pd.DataFrame(dataMain)

    # ---------------------------------
    # 1. Split + explode
    # ---------------------------------
    dataTest['author_list'] = (
        dataTest['Author full names']
        .str.split(';')
    )

    dataTest = (
        dataTest
        .explode('author_list', ignore_index=True)
    )

    dataTest['author_list'] = dataTest['author_list'].str.strip()

    # ---------------------------------
    # 2. Vectorized Clean + Split
    # ---------------------------------
    extracted = dataTest['author_list'].str.extract(
        r'([^,]+),\s*(.+?)\s*\((\d+)\)'
    )

    # extracted columns:
    # 0 = lastname
    # 1 = firstname
    # 2 = number

    dataTest['author_list_number'] = extracted[2]

    dataTest['author_list'] = (
        extracted[0].fillna('') + ' ' + extracted[1].fillna('')
    ).str.strip()

    # ถ้าแถวไหน match ไม่ได้ ให้ใช้ค่าเดิม
    mask = dataTest['author_list'] == ''
    dataTest.loc[mask, 'author_list'] = dataTest.loc[mask, 'Author full names']

    # ---------------------------------
    # 3. Author order (เร็วอยู่แล้ว)
    # ---------------------------------
    dataTest['author_order'] = (
        dataTest.groupby('EID').cumcount() + 1
    )

    dataTest['first_author'] = (
        dataTest['author_order'].eq(1)
        .map({True: "First Author", False: ""})
    )

    # ---------------------------------
    # 4. Clean Source Title (vectorized)
    # ---------------------------------
    dataTest['Source title_clean'] = (
        dataTest['Source title']
        .astype(str)
        .str.replace('\xa0', ' ', regex=False)
        .str.strip()
        .str.lower()
    )

    dataTest['Journal'] = (
        dataTest['Source title_clean']
        .str.contains('journal', na=False)
        .map({True: "journal", False: ""})
    )

    # ---------------------------------
    # Debug
    # ---------------------------------
    # print(len(dataTest.columns))
    # print(dataTest[['author_list','Author Keywords']].head())
    # print(dataTest.info())
    return dataTest

async def call_gemini_batch(batch: list):
    batch = [k for k in batch if k and str(k).strip()]
    if not batch:
        return {}
        
    prompt = f"Standardize these research keywords into high-level 'Expertise Topics': {batch}"
    
    try:
        response = await client.aio.models.generate_content(
            model='gemini-2.0-flash', # Upgraded model
            contents=prompt,
            config={
                'response_mime_type': 'application/json',
                # This ensures the output is a simple flat object
            }
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"Error in batch: {e}")
        return {k: k for k in batch}

async def get_topic_mapping(unique_keywords: list):
    semaphore = asyncio.Semaphore(CONCURRENT_LIMIT)
    async def sem_task(batch):
        async with semaphore:
            return await call_gemini_batch(batch)
    batches = [unique_keywords[i:i + BATCH_SIZE] for i in range(0, len(unique_keywords), BATCH_SIZE)]
    tasks = [sem_task(b) for b in batches]
    results = await asyncio.gather(*tasks)
    final_mapping = {}
    for r in results:
        if isinstance(r, dict):
            final_mapping.update(r)
    return final_mapping

