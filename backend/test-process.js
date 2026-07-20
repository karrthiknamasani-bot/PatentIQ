const fs = require('fs');

const sleep = ms => new Promise(r => setTimeout(r, ms));

async function runTests() {
  console.log("--- Creating dummy files ---");
  fs.writeFileSync('test_long.txt', 'This is a long test document. '.repeat(500)); // ~15000 chars

  // Login
  const loginRes = await fetch('http://localhost:5000/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email: 'test@example.com', password: 'password123' })
  });
  const token = (await loginRes.json()).data.token;

  // Upload TXT
  const formData = new FormData();
  formData.append('title', 'Test Processing TXT');
  formData.append('document', new Blob([fs.readFileSync('test_long.txt')], { type: 'text/plain' }), 'test_long.txt');

  const uploadRes = await fetch('http://localhost:5000/api/projects/upload', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` },
    body: formData
  });
  
  const projectId = (await uploadRes.json()).data._id;
  console.log("Uploaded project ID:", projectId);

  // Trigger processing
  console.log("--- Triggering Process ---");
  const processRes = await fetch(`http://localhost:5000/api/process/${projectId}`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` }
  });
  console.log("Process Triggered:", (await processRes.json()).message);

  // Poll status
  let status = 'processing';
  while(status === 'processing') {
    await sleep(1000);
    const statusRes = await fetch(`http://localhost:5000/api/process/${projectId}/status`, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    const statusData = (await statusRes.json()).data;
    status = statusData.status;
    console.log(`Status: ${status} (Stage: ${statusData.processingStage})`);
    
    if (status === 'failed') {
      console.error("Error:", statusData.errorMessage);
      break;
    }
  }

  // Fetch full project to check chunks
  if (status === 'processed') {
      const projRes = await fetch(`http://localhost:5000/api/projects/${projectId}`, {
          headers: { 'Authorization': `Bearer ${token}` }
      });
      const proj = (await projRes.json()).data;
      console.log("Extraction Length:", proj.extractedText.length);
      console.log("Metadata:", proj.extractedMetadata);
      console.log("Duration:", proj.processingDuration, "ms");
  }
}

runTests().catch(console.error);
