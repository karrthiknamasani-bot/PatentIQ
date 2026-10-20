import httpx
import time
import json

url = 'http://127.0.0.1:8000/api/pipeline/analyze'
headers = {
    'Authorization': 'Bearer patentiq-dev-demo-token-00000000-0000-0000-0000-000000000001'
}

data = {
    'title': 'Autonomous Robotic Surgical System Audit Run',
    'domain': 'Medical Robotics and Surgical Instrumentation',
    'description': 'Real-time tissue compliance and dual-drive articulation.'
}

with open(r'c:\Users\karrt\Downloads\PatentIQ_Final\test_disclosure_audit.txt', 'rb') as f:
    files = {
        'file': ('test_disclosure_audit.txt', f, 'text/plain')
    }

    t0 = time.time()
    print('Starting live pipeline execution against http://127.0.0.1:8000/api/pipeline/analyze...')
    with httpx.Client(timeout=180.0) as client:
        r = client.post(url, headers=headers, data=data, files=files)
        dur = time.time() - t0
        print(f'Pipeline finished in {dur:.2f} seconds with status code {r.status_code}')

        if r.status_code == 200:
            res = r.json()
            proj_id = res.get('project_id')
            print('Project ID:', proj_id)
            print('Chunk Count:', res.get('chunk_count'))
            print('Feature Count:', res.get('feature_count'))
            print(f"Readiness Score: {res.get('readiness_score')} ({res.get('readiness_percentage')} pct) - Category: {res.get('readiness_category')}")
            print('Confidence Score:', res.get('confidence_score'))
            print('Uncertainty Flags:', res.get('uncertainty_flags'))
            print('Dimension Scores:')
            for dim, ddata in res.get('dimension_scores', {}).items():
                print(f"  - {dim:25}: score={ddata.get('score')} | weight={ddata.get('weight')} | conf={ddata.get('confidence')}")
            print('Report Title:', res.get('report', {}).get('title'))
            print('Report Model:', res.get('report', {}).get('model_used'))
            print('Legal Disclaimer Present:', bool(res.get('report', {}).get('legal_disclaimer')))
            
            # Check persistence by retrieving project
            p_url = f"http://127.0.0.1:8000/api/projects/{proj_id}"
            r_p = client.get(p_url, headers=headers)
            print(f'Verification GET project status: {r_p.status_code}')
            if r_p.status_code == 200:
                p_data = r_p.json()
                print('Persisted Project Title:', p_data.get('title'))
                print('Persisted Analysis Score:', p_data.get('readiness_score'))
                print('Persisted Report ID:', p_data.get('report', {}).get('id'))
        else:
            print('Error response:', r.text)
