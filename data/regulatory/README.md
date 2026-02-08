# Regulatory Documents

이 디렉토리는 NGT 안전성 평가 관련 규제 문서를 저장합니다.

## 샘플 PDF 다운로드 링크

실제 운영 환경에서는 아래 공식 문서들을 다운로드하여 사용하세요:

### Codex Alimentarius
- **Guideline for Safety Assessment of Foods Derived from Modern Biotechnology**
  - URL: https://www.fao.org/fao-who-codexalimentarius/sh-proxy/en/?lnk=1&url=https%253A%252F%252Fworkspace.fao.org%252Fsites%252Fcodex%252FStandards%252FCXG%2B44-2003%252FCXG_044e.pdf
  - Source: `Codex`
  - Type: `guideline`
  - Year: `2003` (updated periodically)

### FDA (U.S. Food and Drug Administration)
- **Guidance for Industry: Voluntary Labeling Indicating Whether Foods Have or Have Not Been Derived from Genetically Engineered Plants**
  - URL: https://www.fda.gov/regulatory-information/search-fda-guidance-documents
  - Source: `FDA`
  - Type: `guidance`

### EFSA (European Food Safety Authority)
- **Guidance on risk assessment of food and feed from genetically modified plants**
  - URL: https://www.efsa.europa.eu/en/efsajournal/pub/6301
  - Source: `EFSA`
  - Type: `guideline`

### FSANZ (Food Standards Australia New Zealand)
- **Safety Assessment of Genetically Modified Foods**
  - URL: https://www.foodstandards.gov.au/publications/Pages/Safety-assessment-of-genetically-modified-foods.aspx
  - Source: `FSANZ`
  - Type: `guideline`

## 사용 예시

PDF 다운로드 후:

```bash
# PDF 처리
python -m rag.cli process \
  --file data/regulatory/codex_gm_foods.pdf \
  --source Codex \
  --type guideline \
  --year 2003

# 처리 결과 확인
python -m rag.cli stats

# 검색 테스트
python -m rag.cli query "safety assessment procedures"
```

## 테스트용 파일

- `sample.txt`: 테스트용 샘플 텍스트 (ChromaDB 없이 청킹 검증 가능)

## 저작권 안내

위 문서들은 각 기관의 공식 자료이며, 교육 및 연구 목적으로만 사용하세요.
