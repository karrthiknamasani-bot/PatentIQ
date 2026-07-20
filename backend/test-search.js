const fs = require('fs');

async function runTests() {
  // Login
  const loginRes = await fetch('http://localhost:5000/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email: 'test@example.com', password: 'password123' })
  });
  const loginData = await loginRes.json();
  const token = loginData.data.token;

  console.log("--- Creating a new Patent via Import to trigger Embeddings ---");
  const dummyCsv = `patentNumber,title,abstract,inventors,assignee,publicationDate,ipcClasses,source\nUS_CHROMA_01,Machine Learning Vector Database,A database specialized in storing floating point vector embeddings for AI semantic search.,AI Engineer,,2025-01-01,,uspto`;
  fs.writeFileSync('test_chroma_patent.csv', dummyCsv);

  const formDataCsv = new FormData();
  formDataCsv.append('file', new Blob([fs.readFileSync('test_chroma_patent.csv')], { type: 'text/csv' }), 'test_chroma_patent.csv');
  
  const csvRes = await fetch('http://localhost:5000/api/patents/import', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` },
    body: formDataCsv
  });
  
  console.log("Patent Import triggered:", await csvRes.json());
  
  console.log("--- Waiting for async embeddings to generate (5 seconds) ---");
  await new Promise(r => setTimeout(r, 5000));

  console.log("--- Testing Semantic Search ---");
  const searchRes = await fetch('http://localhost:5000/api/search/similar', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query: 'database for storing vectors', topK: 3 })
  });
  
  const searchData = await searchRes.json();
  console.log("Semantic Search Success:", searchData.success);
  console.log("Search Results from ChromaDB:");
  
  if (searchData.data && searchData.data.documents) {
    const docs = searchData.data.documents[0];
    const metas = searchData.data.metadatas[0];
    
    docs.forEach((doc, idx) => {
        console.log(`[Result ${idx + 1}] Source: ${metas[idx].sourceType} | Text: ${doc}`);
    });
  } else {
    console.log(searchData);
  }
}

runTests().catch(console.error);
