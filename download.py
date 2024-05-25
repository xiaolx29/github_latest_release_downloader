import requests

from submodule_reattempt import ReAttempt

def get_response(**kwargs):
    response = requests.get(**kwargs)
    response.raise_for_status()
    return response

re_attempt = ReAttempt(
    max_retries=3,
    acceptable_exception=(
        requests.exceptions.Timeout, 
        requests.exceptions.RequestException
    ))

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36(KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
owner = input('owner:')
repo = input('repo:')
github_url = 'https://api.github.com/repos/{}/{}/releases/latest'.format(owner, repo)
print('Trying to get response from github')
success, github_response = re_attempt.run(get_response, url = github_url, timeout = 10)
if success:
    print(github_response.json()['assets'])
