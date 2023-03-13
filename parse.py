import json
from time import sleep
from shutil import unpack_archive
from os import listdir, remove
from os.path import dirname, abspath, join
from tqdm import tqdm
from prettytable import PrettyTable
from selenium import webdriver
from selenium.webdriver.common.by import By

ROOT_DIR = dirname(abspath(__file__))
RESULT_DIR = join(ROOT_DIR, 'results')
URL = 'https://euclid.eba.europa.eu/register/pir/registerDownload'


def get_by_filename(extension, folder):
    return join(folder,
                [f for f in listdir(folder) if f.endswith(extension)][0])


def cleanup():
    print('Cleaning up old files... ')
    files = [join(ROOT_DIR, f)
             for f in listdir(ROOT_DIR) if f.split('.')[-1] in ('json', 'sha256')]
    for file in files:
        remove(file)


def get_countries():
    with open(join(ROOT_DIR, 'countries.csv'), 'r') as data:
        return dict(foo[:-1].split(',') for foo in data.readlines())


def download():
    # EBA site does not provide direct download link in the HTML page,
    # user is redirected to file after clicking the button, therefore,
    # regular website scraping does not work. To bypass this, Selenium
    # is used to emulate Chromium browser.
    # The Easiest way to use this script is to use Docker to avoid
    # setting up Selenium on your own machine

    print('Starting Browser...')
    # Setup Chromium options:
    options = webdriver.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')

    # Start Browser
    browser = webdriver.Chrome(options=options)
    print('Opening URL...')
    browser.get(URL)
    # Wait so page has time to load
    sleep(20)

    # Xpath describes button location on the website
    xpath = '/html/body/app-root/app-pir/div[1]/div/app-app-register-download/div/p-card/div/div/div/form/div[4]/div/p-button/button'
    download_button = browser.find_element(By.XPATH, xpath)
    browser.execute_script('arguments[0].click();', download_button)
    sleep(20)
    browser.close()

    print('Extracting files...')
    # Get Archive
    zip_file = get_by_filename('.zip', ROOT_DIR)

    unpack_archive(zip_file, ROOT_DIR)
    remove(zip_file)

    print('Exited successfully')


def process_data():
    data_file = get_by_filename('.json', ROOT_DIR)
    print('Reading data...')
    with open(data_file) as data:
        parsed_json = json.load(data)
    companies = parsed_json[1]
    countries = {}

    sum_of_services = 0
    service_companies = 0

    acc_info_services = 0
    payment_init_services = 0

    print('Processing data...')
    for it in tqdm(range(len(companies))):
        company = companies[it]
        country_name = [list(*f.items())[1]
                        for f in company.get('Properties') if f.get('ENT_COU_RES')][0]
        if country_name in countries:
            countries[country_name] += 1
        else:
            countries[country_name] = 1
        if company.get('Services'):
            sum_of_services += len(company['Services'])
            service_companies += 1

            # Companies can be certified to do the same services in multiple countries
            # therefore they are counted only once
            payment_init_service_found = False
            acc_info_service_found = False
            for s in company['Services']:
                # If there is a single instance of a service,
                # it is represented as a string rather than a list
                # This line extracts value to str or list from dictvalues type
                service = list(s.values())[0]
                if type(service) == str:
                    # If type is string, add it to the list, for simplicity
                    service = [service]

                if 'PS_070' in service and not payment_init_service_found:
                    payment_init_services += 1
                    payment_init_service_found = True
                if 'PS_080' in service and not acc_info_service_found:
                    acc_info_services += 1
                    acc_info_service_found = True

                # If both instances found, stop itterating
                if acc_info_service_found and payment_init_service_found:
                    break
    most_companies = sorted(list(countries.items()),
                            key=lambda x: x[1], reverse=True)[0]
    return {
        'total': len(companies),
        'percentage_of_service': service_companies/len(companies),
        'service_companies': service_companies,
        'avg_service_countries': sum_of_services/service_companies,
        'top_country_name': most_companies[0],
        'top_country_count': most_companies[1],
        'acc_info_amount': acc_info_services,
        'payment_init_amount': payment_init_services
    }


if __name__ == '__main__':
    download()
    results = process_data()
    countries = get_countries()
    t = PrettyTable()
    t.field_names = ['Key', 'Value']
    t.add_rows(
        [
            ['Total Companies', results['total']],
            ['Total Companies Providing Services', results['service_companies']],
            ['Percentage of Service Companies', '{:.2f}'.format(
                results['percentage_of_service'] * 100)],
            ['Avg Served Countries', round(
                results['avg_service_countries'], 2)],
            ['Country w/ Most Registered Companies',
             countries[results['top_country_name']]],
            ['Companies Registered in Top Country', results['top_country_count']],
            ['Companies w/ Access to "Account information services"',
             results['acc_info_amount']],
            ['Companies w/ Access to "Payment initiation services"',
             results['payment_init_amount']]
        ]
    )
    print(t)
    cleanup()
    with open(join(RESULT_DIR, 'results.json'), 'w') as output:
        json.dump(results, output, indent=2)
