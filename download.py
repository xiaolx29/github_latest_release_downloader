import os, re, argparse, configparser
import requests
from tqdm import tqdm
from submodule_reattempt import ReAttempt

def get_response(**kwargs) -> requests.Response:
    response = requests.get(**kwargs)
    response.raise_for_status()
    return response

def download_with_progress(response: requests.Response, filename: str) -> None:
    total_size = int(response.headers.get('content-length', 0))
    progress_bar = tqdm(total = total_size, unit = 'B', unit_scale = True, desc = 'Downloading')
    with open(filename, mode = 'wb') as file:
        for chunk in response.iter_content(chunk_size = 1024):
            file.write(chunk)
            progress_bar.update(len(chunk))
    progress_bar.close()

parser = argparse.ArgumentParser(description = 'Download software')
group = parser.add_mutually_exclusive_group(required = True)
group.add_argument('-n', '--names', type = str, nargs = '*', help = 'download by name.', metavar = 'NAME')
group.add_argument('-a', '--all', action = 'store_true', help = 'download all available.')
args = parser.parse_args()

config = configparser.ConfigParser()
config.read('config.ini')
github_link_format = config.get(section = 'General', option = 'GithubLinkFormat')
headers = {'User-Agent': config.get(section = 'General', option = 'User-Agent')}
retries = config.getint(section = 'General', option = 'RetryTimes')
timeout = config.getfloat(section = 'General', option = 'Timeout')

re_attempt = ReAttempt(
    max_retries=3,
    acceptable_exception=(
        requests.exceptions.Timeout, 
        requests.exceptions.RequestException
    ),
    on_success = lambda retry_index, result: tqdm.write('Attempt {}: Result: {}.'.format(retry_index + 1, result)),
    on_exception = lambda retry_index, exception: tqdm.write('Attempt {}: Exception: {}{}'.format(retry_index + 1, type(exception), exception))
    )

# list of programs user choose to download
program_names = [name for name in config.sections() if name != 'General'] if args.all else args.names

for name in program_names:
    tqdm.write('Handling {}.'.format(name))
    if name not in config.sections():
        tqdm.write('illegal software name: {}.'.format(name))
        continue
    owner = config.get(section = name, option = 'GithubRepoOwner')
    repo = config.get(section = name, option = 'GithubRepoName')
    download_url_pattern = config.get(section = name, option = 'DownloadUrlPattern')
    github_link = github_link_format.format(owner = owner, repo = repo)
    tqdm.write('Trying to get download link from Github.')
    success, github_response = re_attempt.run(func = get_response, url = github_link, headers = headers, timeout = timeout)
    if success:  # can get response from github
        for asset in github_response.json()['assets']:
            download_url = asset['browser_download_url']
            if re.match(pattern = download_url_pattern, string = download_url):
                break
        else:  # can not find any download url that matches the pattern
            tqdm.write('Can not find download link that matches the pattern {}.'.format(download_url_pattern))
    
    tqdm.write('Trying to download {} at {}.'.format(name, download_url))
    success, download_response = re_attempt.fun(func = get_response, url = download_url, headers = headers, timeout = timeout, stream = True)
    if success:  # can download
        save_path = config.get(section = name, option = 'SavePath')
        download_with_progress(download_response, os.path.join(save_path, download_url.split('/')[-1]))
    else:  # can not get response
        tqdm.write('Can not download {}.'.format(name, download_url))

