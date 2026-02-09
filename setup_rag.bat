@echo off
echo ============================================================
echo Virtual Lab RAG Setup (Pinecone)
echo ============================================================
echo.

echo [1/3] Installing packages...
pip install pinecone-client>=3.0.0 PyPDF2>=3.0.0
echo.

echo [2/3] Loading PDFs to Pinecone...
python load_pdfs_to_pinecone.py
echo.

echo [3/3] Testing RAG search...
python -c "from tools.rag_search import rag_search_tool; result = rag_search_tool.invoke({'query': 'allergen assessment'}); print('\n=== Test Result ==='); print(result[:500] + '...')"
echo.

echo ============================================================
echo Setup Complete!
echo ============================================================
echo.
echo Next: Start the server
echo   uvicorn server:app --reload --port 8000
echo.
pause
