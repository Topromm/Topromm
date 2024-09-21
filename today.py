from dateutil import relativedelta
from xml.dom import minidom
import requests
import datetime
import hashlib
import random
import json
import time
import os

# Personal access token with permissions: read:enterprise, read:org, read:repo_hook, read:user, repo
HEADERS = {'authorization': 'token '+ os.environ['ACCESS_TOKEN']}
USER_NAME = os.environ['USER_NAME'] # 'Andrew6rant'
QUERY_COUNT = {'user_getter': 0}


def daily_readme(birthday):
    """
    Returns the length of time since I was born
    e.g. 'XX years, XX months, XX days'
    """
    diff = relativedelta.relativedelta(datetime.datetime.today(), birthday)
    return '{} {}, {} {}, {} {}{}'.format(
        diff.years, 'year' + format_plural(diff.years), 
        diff.months, 'month' + format_plural(diff.months), 
        diff.days, 'day' + format_plural(diff.days),
        ' 🎂' if (diff.months == 0 and diff.days == 0) else '')


def format_plural(unit):
    """
    Returns a properly formatted number
    e.g.
    'day' + format_plural(diff.days) == 5
    >>> '5 days'
    'day' + format_plural(diff.days) == 1
    >>> '1 day'
    """
    return 's' if unit != 1 else ''

def get_random_joke(jokes_file):
    with open(jokes_file, 'r') as f:
        jokes = json.load(f)
    return random.choice(jokes)

def simple_request(func_name, query, variables):
    """
    Returns a request, or raises an Exception if the response does not succeed.
    """
    request = requests.post('https://api.github.com/graphql', json={'query': query, 'variables':variables}, headers=HEADERS)
    if request.status_code == 200:
        return request
    raise Exception(func_name, ' has failed with a', request.status_code, request.text, QUERY_COUNT)

def svg_overwrite(filename, age_data, joke):
    """
    Parse SVG files and update elements with my age, commits, stars, repositories, and lines written
    """
    svg = minidom.parse(filename)
    f = open(filename, mode='w', encoding='utf-8')
    tspans = svg.getElementsByTagName('tspan')
    # tspan[32].firstChild.data = age_data

    uptime_index = None
    for i, tspan in enumerate(tspans):
        if tspan.firstChild and 'Uptime' in tspan.firstChild.data:
            uptime_index = i
            break

    # Check if 'Uptime' tspan is found
    if uptime_index is not None and uptime_index + 1 < len(tspans):
        # Update the next tspan element after 'Uptime'
        tspans[uptime_index + 1].firstChild.data = age_data
    else:
        print("Uptime information not found or unable to update.")

    f.write(svg.toxml('utf-8').decode('utf-8'))
    f.close()

    # Replace the joke in the README.md
    with open('README.md', 'r+', encoding='utf-8') as readme_file:
        content = readme_file.readlines()
        # Find the line with the marker and replace it with the new joke
        for i, line in enumerate(content):
            if '<!-- JOKE HERE -->' in line:
                content[i] = f"### Awful Joke of the Day\n{joke}\n"
                break
        else:
            # If marker not found, append the joke at the end (as a fallback)
            content.append(f"\n### Awful Joke of the Day\n{joke}\n")

        readme_file.seek(0)
        readme_file.writelines(content)
        readme_file.truncate()  # Ensure the file is truncated to the new size

def svg_element_getter(filename):
    """
    Prints the element index of every element in the SVG file
    """
    svg = minidom.parse(filename)
    open(filename, mode='r', encoding='utf-8')
    tspan = svg.getElementsByTagName('tspan')
    for index in range(len(tspan)): print(index, tspan[index].firstChild.data)


def user_getter(username):
    """
    Returns the account ID and creation time of the user
    """
    query_count('user_getter')
    query = '''
    query($login: String!){
        user(login: $login) {
            id
            createdAt
        }
    }'''
    variables = {'login': username}
    request = simple_request(user_getter.__name__, query, variables)
    return {'id': request.json()['data']['user']['id']}, request.json()['data']['user']['createdAt']

def query_count(funct_id):
    """
    Counts how many times the GitHub GraphQL API is called
    """
    global QUERY_COUNT
    QUERY_COUNT[funct_id] += 1


def perf_counter(funct, *args):
    """
    Calculates the time it takes for a function to run
    Returns the function result and the time differential
    """
    start = time.perf_counter()
    funct_return = funct(*args)
    return funct_return, time.perf_counter() - start


def formatter(query_type, difference, funct_return=False, whitespace=0):
    """
    Prints a formatted time differential
    Returns formatted result if whitespace is specified, otherwise returns raw result
    """
    print('{:<23}'.format('   ' + query_type + ':'), sep='', end='')
    print('{:>12}'.format('%.4f' % difference + ' s ')) if difference > 1 else print('{:>12}'.format('%.4f' % (difference * 1000) + ' ms'))
    if whitespace:
        return f"{'{:,}'.format(funct_return): <{whitespace}}"
    return funct_return


if __name__ == '__main__':
    print('Calculation times:')
    age_data, age_time = perf_counter(daily_readme, datetime.datetime(2003, 5, 13))
    formatter('age calculation', age_time)

    joke = get_random_joke('jokes.json')
    svg_overwrite('dark_mode.svg', age_data, joke)
    svg_overwrite('light_mode.svg', age_data, joke)

