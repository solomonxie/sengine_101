class BaseScraper:
    def __init__(self, url):
        assert url not in ['', None], 'SHOULD GIVE URL'
        self.url = url

    def start(self):
        pass


def main():
    pass


if __name__ == '__main__':
    main()
