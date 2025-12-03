import requests, json, sys

def main():
    base = 'http://127.0.0.1:5000'
    print('Testing', base)
    try:
        print('\nPOST /api/chat')
        r = requests.post(base + '/api/chat', json={'message':'smoke test from script'})
        print('Status:', r.status_code)
        try:
            print('Response JSON:', json.dumps(r.json(), indent=2))
        except Exception:
            print('Response text:', r.text)

        print('\nGET /api/chats')
        r2 = requests.get(base + '/api/chats')
        print('Status:', r2.status_code)
        try:
            docs = r2.json()
            print('Chats count:', len(docs) if isinstance(docs, list) else 'N/A')
            print('Sample:', json.dumps(docs[:2], indent=2))
        except Exception:
            print('Response text:', r2.text)

    except Exception as e:
        print('Error during smoke tests:', e)
        sys.exit(2)

if __name__ == '__main__':
    main()
