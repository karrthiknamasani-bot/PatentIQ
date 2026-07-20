const fs = require('fs');

async function runTests() {
  console.log("--- Creating dummy patent files ---");
  
  const dummyCsv = `patentNumber,title,abstract,inventors,assignee,publicationDate,ipcClasses,source
US1234567,Test Patent One,This is a test abstract for patent one. It has some text.,John Doe;Jane Smith,TechCorp,2023-01-01,G06F 17/30;H04L 29/06,uspto
US7654321,Test Patent Two,Another test abstract for the second patent.,Alice Bob,InnovateInc,2022-05-15,A61K 31/00,epo`;
  fs.writeFileSync('test_patents.csv', dummyCsv);

  const dummyJson = [
    {
      "patentNumber": "WO2023000001",
      "title": "Global Patent Alpha",
      "abstract": "An abstract for a global patent from WIPO.",
      "inventors": ["Global Inventor"],
      "assignee": "GlobalTech",
      "publicationDate": "2023-11-10",
      "ipcClasses": ["G06Q 50/00"],
      "source": "wipo",
      "metadata": { "url": "http://example.com/patent" }
    }
  ];
  fs.writeFileSync('test_patents.json', JSON.stringify(dummyJson));

  // Login
  const loginRes = await fetch('http://localhost:5000/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email: 'test@example.com', password: 'password123' })
  });
  const token = (await loginRes.json()).data.token;

  console.log("--- Importing CSV ---");
  const formDataCsv = new FormData();
  formDataCsv.append('file', new Blob([fs.readFileSync('test_patents.csv')], { type: 'text/csv' }), 'test_patents.csv');
  
  const csvRes = await fetch('http://localhost:5000/api/patents/import', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` },
    body: formDataCsv
  });
  const csvData = await csvRes.json();
  console.log("CSV Import Response:", csvData.success ? csvData.message : csvData);

  console.log("--- Importing JSON ---");
  const formDataJson = new FormData();
  formDataJson.append('file', new Blob([fs.readFileSync('test_patents.json')], { type: 'application/json' }), 'test_patents.json');
  
  const jsonRes = await fetch('http://localhost:5000/api/patents/import', {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` },
    body: formDataJson
  });
  const jsonData = await jsonRes.json();
  console.log("JSON Import Response:", jsonData.success ? jsonData.message : jsonData);

  console.log("--- Fetch All Patents ---");
  const allRes = await fetch('http://localhost:5000/api/patents', {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  const allData = await allRes.json();
  console.log("Total Patents DB Count:", allData.data.total);

  if (allData.data.patents.length > 0) {
      const firstId = allData.data.patents[0]._id;
      console.log("--- Fetch Single Patent ---");
      const singleRes = await fetch(`http://localhost:5000/api/patents/${firstId}`, {
          headers: { 'Authorization': `Bearer ${token}` }
      });
      const singleData = await singleRes.json();
      console.log(`Single Patent: ${singleData.data.patentNumber} - ${singleData.data.title}`);
      console.log(`Generated Chunks: ${singleData.data.chunks.length}`);
  }
}

runTests().catch(console.error);
