const fs = require('fs');

async function runTests() {
  // Login
  const loginRes = await fetch('http://localhost:5000/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email: 'test@example.com', password: 'password123' })
  });
  const token = (await loginRes.json()).data.token;

  console.log("--- Creating a new project for Analysis ---");
  fs.writeFileSync('test_analysis_project.txt', 'This is a brand new project about a vector database designed specifically for patent retrieval using semantic search and Agentic RAG.');
  const formData = new FormData();
  formData.append('title', 'Vector Patent Retrieval System');
  formData.append('document', new Blob([fs.readFileSync('test_analysis_project.txt')], { type: 'text/plain' }), 'test_analysis_project.txt');

  const uploadRes = await fetch('http://localhost:5000/api/projects/upload', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` },
    body: formData
  });
  const project = (await uploadRes.json()).data;
  console.log("Project created:", project._id);

  console.log("--- Processing Project ---");
  await fetch(`http://localhost:5000/api/process/${project._id}`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` }
  });

  // Wait for processing and embeddings to complete
  console.log("Waiting 5 seconds for processing and embedding generation...");
  await new Promise(r => setTimeout(r, 5000));

  console.log("--- Running Agentic RAG Analysis ---");
  const analyzeRes = await fetch(`http://localhost:5000/api/analyze/${project._id}`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` }
  });
  
  const analyzeData = await analyzeRes.json();
  console.log("Analysis Triggered. Success:", analyzeData.success);

  if (analyzeData.success) {
    console.log("Analysis Scores:", analyzeData.data.scores);
    console.log("Recommendation:", analyzeData.data.analysis.recommendation);
    console.log("Processing Time (ms):", analyzeData.data.processingTimeMs);
  } else {
    console.log(analyzeData);
  }
}

runTests().catch(console.error);
