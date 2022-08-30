import json, os

current_path = os.path.dirname(__file__)
path = current_path + '/../fixtures/devQualityApi.json'
file = open(path, 'r')
json_data = file.read()
file.close()

data = json.loads(json_data)
response = []
count = 0
for d in data:
    if d['model'] == 'auth.user':
        count += 1
        d['fields'] = {'password': 'pbkdf2_sha256$20000{0}'.format(count),
                       'is_superuser': False, 'username': 'user{0}'.format(count),
                       'first_name': 'User {0}'.format(count), 'last_name': '', 'email': '',
                       'is_active': True, 'groups': [],
                       'user_permissions': []}
    response.append(d)


response_file = open(current_path + '/anonymized_data.json', 'w')
response_file.write(json.dumps(response, indent=2))
response_file.close()
