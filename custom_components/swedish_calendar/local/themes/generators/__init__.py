from datetime import date

count_descriptors = ['Första', 'Andra', 'Tredje', 'Fjärde', 'Femte', 'Sjätte']


class ThemeDateGenerator:

    def matches(self, theme: str, dates: [date]) -> bool:
        return False

    def generate_config(self, theme: str, dates: [date]) -> dict[str, any]:
        return {
            'theme': theme,
            'generator': self.name(),
            'description': ''
        }

    def generate(self, config: dict[str, any], year: int) -> date:
        print(config['description'])
        raise Exception('Not implemented')

    def name(self) -> str:
        raise Exception('No name provided')
