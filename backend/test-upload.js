const fs = require('fs');

async function runTests() {
  console.log("--- Creating dummy files ---");
  fs.writeFileSync('test.pdf', 'PDF dummy content');
  fs.writeFileSync('test.csv', 'CSV dummy content');

  console.log("--- 1. Login to get token ---");
  const loginRes = await fetch('http://localhost:5000/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email: 'test@example.com', password: 'password123' })
  });
  const loginData = await loginRes.json();
  const token = loginData.data.token;
  console.log("Token received.");

  console.log("--- 2. Test unauthorized upload ---");
  const unauthRes = await fetch('http://localhost:5000/api/projects/upload', {
    method: 'POST',
    body: new FormData()
  });
  console.log("Unauthorized upload status:", unauthRes.status); // should be 401

  console.log("--- 3. Test invalid upload (CSV) ---");
  const badFormData = new FormData();
  badFormData.append('title', 'Bad File Project');
  const badFileBlob = new Blob([fs.readFileSync('test.csv')], { type: 'text/csv' });
  badFormData.append('document', badFileBlob, 'test.csv');

  const badUploadRes = await fetch('http://localhost:5000/api/projects/upload', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` },
    body: badFormData
  });
  console.log("Invalid upload status:", badUploadRes.status); // should be 500 or 400

  console.log("--- 4. Test valid upload (PDF) ---");
  const goodFormData = new FormData();
  goodFormData.append('title', 'Valid PDF Project');
  goodFormData.append('description', 'Test desc');
  const goodFileBlob = new Blob([fs.readFileSync('test.pdf')], { type: 'application/pdf' });
  goodFormData.append('document', goodFileBlob, 'test.pdf');

  const uploadRes = await fetch('http://localhost:5000/api/projects/upload', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` },
    body: goodFormData
  });
  const uploadData = await uploadRes.json();
  console.log("Valid upload response:", uploadData.success, uploadData.message);
  
  if (!uploadData.success) {
      console.error(uploadData);
      return;
  }
  
  const projectId = uploadData.data._id;
  console.log("Project ID created:", projectId);

  console.log("--- 5. Fetch all projects ---");
  const allRes = await fetch('http://localhost:5000/api/projects', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  const allData = await allRes.json();
  console.log("Total projects fetched:", allData.data.length);

  console.log("--- 6. Fetch single project ---");
  const singleRes = await fetch(`http://localhost:5000/api/projects/${projectId}`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  const singleData = await singleRes.json();
  console.log("Single project title:", singleData.data.title);

  console.log("--- 7. Delete project ---");
  const deleteRes = await fetch(`http://localhost:5000/api/projects/${projectId}`, {
    method: 'DELETE',
    headers: { 'Authorization': `Bearer ${token}` }
  });
  const deleteData = await deleteRes.json();
  console.log("Delete response:", deleteData.message);

  console.log("--- Done ---");
}

runTests().catch(console.error);
