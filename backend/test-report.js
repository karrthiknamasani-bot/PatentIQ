const fs = require('fs');
const path = require('path');

async function runTests() {
  // Login
  const loginRes = await fetch('http://localhost:5000/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email: 'test@example.com', password: 'password123' })
  });
  const token = (await loginRes.json()).data.token;

  // Get Projects
  const projectsRes = await fetch('http://localhost:5000/api/projects', {
    method: 'GET',
    headers: { 'Authorization': `Bearer ${token}` }
  });
  const projects = (await projectsRes.json()).data;
  const project = projects.find(p => p.status === 'processed');

  if (!project) {
    console.log("No processed project found. Run test-analyze.js first.");
    return;
  }

  console.log(`Using Project: ${project.title} (${project._id})`);

  console.log("--- Generating PDF Report ---");
  const pdfRes = await fetch(`http://localhost:5000/api/report/${project._id}`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ type: 'pdf' })
  });
  const pdfData = await pdfRes.json();
  console.log("PDF Generation Success:", pdfData.success);
  console.log("PDF Report Record:", pdfData.data._id);

  console.log("--- Generating JSON Report ---");
  const jsonRes = await fetch(`http://localhost:5000/api/report/${project._id}`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ type: 'json' })
  });
  const jsonData = await jsonRes.json();
  console.log("JSON Generation Success:", jsonData.success);
  
  console.log("--- Fetching Project Reports History ---");
  const historyRes = await fetch(`http://localhost:5000/api/report/project/${project._id}`, {
    method: 'GET',
    headers: { 'Authorization': `Bearer ${token}` }
  });
  const historyData = await historyRes.json();
  console.log(`Found ${historyData.data.length} reports in history.`);

  console.log("--- Testing Download Endpoint (PDF) ---");
  const downloadRes = await fetch(`http://localhost:5000/api/report/${pdfData.data._id}`, {
    method: 'GET',
    headers: { 'Authorization': `Bearer ${token}` }
  });
  
  if (downloadRes.ok) {
    console.log("Download endpoint successfully returned the file buffer!");
    const arrayBuffer = await downloadRes.arrayBuffer();
    console.log(`File size: ${arrayBuffer.byteLength} bytes`);
  } else {
    console.log("Download failed:", await downloadRes.json());
  }

  // Check uploads folder
  const files = fs.readdirSync(path.join(__dirname, 'uploads/reports'));
  console.log("Files generated in uploads/reports directory:", files);
}

runTests().catch(console.error);
