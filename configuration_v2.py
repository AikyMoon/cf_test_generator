from __future__ import annotations
from random import choice, randint
from pprint import pprint
from typing import NewType, TypeAlias
from termcolor import colored
from benedict import benedict
from prettytable import PrettyTable

import json
import os



class IntGenerator:
    """
    Генератор чисел
    """
    generator_type = int

    def __init__(self, min_value: int, max_value: int) -> None:
        self.min_value = min_value
        self.max_value = max_value
        self.last_state = None
        super().__init__()
        
    

    def generate(self) -> int:
        self.last_state = randint(self.min_value, self.max_value)
        return self.last_state


    def __str__(self) -> str:
        return f"Числа на интервале [{self.min_value}, {self.max_value}]"
    

    def __repr__(self) -> str:
        return f"Числа на интервале [{self.min_value}, {self.max_value}]"
    

class CharGenerator:
    """
    Генератора символов
    """

    generator_type = str

    def __init__(self, valid_chars: str | list[str]) -> None:
        self.valid_chars = valid_chars
        self.last_state = None

    
    def generate(self) -> str:
        self.last_state = choice(self.valid_chars)
        return self.last_state
    
    def __str__(self) -> str:
        return f"Символ из \'{self.valid_chars}\'"
    


class SequenceGenerator:
    """
    Генератор последовательностей
    """

    default_separators = {
        IntGenerator: " ",
        CharGenerator: ""
    }

    def __init__(self, element_generator: IntGenerator | CharGenerator, len_generator: IntGenerator, len_by_var: bool = True, sep: str = None) -> None:
        self.element_generator = element_generator
        self.len_generator = len_generator
        self.len_by_var = len_by_var
        self.sep = sep

        if sep is None:
            elements_type = type(element_generator)
            self.sep = self.default_separators[elements_type]


    def generate(self) -> str:
        seq_len = self.len_generator.last_state if self.len_by_var else self.len_generator.generate()
        seq = [self.element_generator.generate() for _ in range(seq_len)]
        seq = self.sep.join(map(str, seq))

        return seq


    def __str__(self) -> str:
        return f"Последовательность из : {self.element_generator}. Длина {'по переменной' if self.len_by_var else 'случайная'}"
    

# кастомные типы данных
Generators: TypeAlias = IntGenerator | CharGenerator | SequenceGenerator
GroupDescription: TypeAlias = dict[int, dict[str, Generators]]





class Configuration:
    """
    Парсер конфигурации из .json
    """


    # типы генераторов
    generators_types: dict[str, Generators] = {
        "int": IntGenerator,
        "char": CharGenerator,
        "list": SequenceGenerator
    }
    

    def __init__(self, config_path: str) -> None:
        # основные переменные для конфигарации
        self.config_name = None
        self.config_path = config_path
        self.output_format: dict = None
        self.groups: GroupDescription = {}
        self.groups_samples: dict[int, int] = {}

        self.__parse()

    
    def __parse(self) -> None:
        d = {}
        with open(self.config_path, 'r') as fin:
            d = benedict(json.load(fin))
        

        # именование конфигурации
        self.config_name = d["config_name"]
        self.output_format = {int(key): val for key, val in d["output_format"].items()}



        # информация о кол-ве тестов дл каждой подруппы
        for group, sample in d["samples"].items():
            group = int(group)
            self.groups_samples[group] = sample

        

        # заполнение генераторов переменных
        for group in map(int, d["groups"].keys()):
            self.groups[group] = {}

            for var, attrs in d[f"groups.{group}"].items():
                gen = self.config_vars_generators(group, attrs["type"], attrs["optional"])
                self.groups[group][var] = gen
                
    
    
    # конфигурация генераторов переменных
    def config_vars_generators(self, group: int, var_dtype: str, attrs: dict[str, str | int]) -> Generators:
        optional = {}


        # генератор чисел
        if var_dtype == "int":   
            optional["min_value"] = attrs["min"]
            optional["max_value"] = attrs["max"]

        # генератор символов
        elif var_dtype == "char":
            optional["valid_chars"] = attrs["valid_chars"]
        
        # генератор последовательностей
        elif var_dtype == "list":
            element_optional = {}
            subtype = attrs["element_type"]
            seq_len = attrs["len"]


            # определение генератора элементов
            if subtype == "int":
                element_optional["min_value"] = attrs["min"]
                element_optional["max_value"] = attrs["max"]
                optional["element_generator"] = self.generators_types[subtype](**element_optional)
            
            elif subtype == "char":
                element_optional["valid_chars"] = attrs["valid_chars"]
                optional["element_generator"] = self.generators_types[subtype](**element_optional)
            

            # определение параметров генератора длины последовательности
            if isinstance(seq_len, str):
                gen = self.groups[group][seq_len]
                optional["len_generator"] = gen
                optional["len_by_var"] = True

            elif isinstance(seq_len, int):
                gen_optional = {}
                gen_optional["min_value"] = attrs["len"]
                gen_optional["max_value"] = attrs["len"]
                optional["len_generator"] = self.generators_types["int"](**gen_optional)
                optional["len_by_var"] = False

            else:
                gen_optional = {}
                gen_optional["min_value"] = attrs["len.min"]
                gen_optional["max_value"] = attrs["len.max"]
                optional["len_generator"] = self.generators_types["int"](**gen_optional)
                optional["len_by_var"] = False



        return self.generators_types[var_dtype](**optional)


    
    def show_info(self) -> None:
        groups = PrettyTable(field_names=["Group", "N_samples"])
        groups.title = "Краткое описание тест-конфига"
        acc = 0

        for group, sample in self.groups_samples.items():
            groups.add_row([group, sample])
            acc += sample

        print(groups)
        print(f"Всего тестов: {acc}")



class TestcaseGenerator:
    def __init__(self, testcase_dir: str, configuration: Configuration) -> None:
        self.testcase_dir: str = testcase_dir[:-1] if testcase_dir[-1] == "/" else testcase_dir
        self.conf: Configuration = configuration
        self.conf_name = self.conf.config_name

        if not os.path.exists(f"{self.testcase_dir}/{self.conf_name}/"):
            os.mkdir(f"{self.testcase_dir}/{self.conf_name}/")
    

    def generate(self) -> None:
        for group, sample in self.conf.groups_samples.items():
            for i in range(sample):
                output = {}

                for line_num, desc in self.conf.output_format.items():
                    dump = []

                    repeat = desc["repeat"]
                    repeat_var = 1 if repeat is None else self.conf.groups[group][repeat].last_state
                    

                    # генерация repeat_var запросов
                    for _ in range(repeat_var):
                        dump_line = []

                        # генерация данных из генератора
                        for var in desc["vars"]:
                            value = str(self.conf.groups[group][var].generate())
                            dump_line.append(value)
                        dump.append(tuple(dump_line))

                    
                    output[line_num] = {"dump": dump, "sep": desc["sep"]}


                filename = f"{self.conf_name}_{group}_{i + 1}.txt"
                # pprint(output)
                self.generate_dump(filename, output)
                print(colored(f"Тест: {filename} успешно сгенерирован", "green"))
            print(colored(f"Подгруппа: {group} успешно сгенерирована", "yellow"))
            print()

    
    def generate_dump(self, filename: str, output_data: dict[int, tuple[str]]) -> None:
        filepath = f"{self.testcase_dir}/{self.conf_name}/{filename}"

        # запись теста в файл
        with open(filepath, 'w') as fin:
            for key, data in sorted(output_data.items(), key=lambda x: x[0]):
                line_dump = ""

                # добавление сепараторов между переменными
                if data["sep"] is None:
                    for el in data["dump"]:
                        line_dump += " ".join(el) + "\n"
                else:
                    sep = data["sep"]
                    dump = data["dump"]
                    for line in dump:
                        for i in range(len(sep)):
                            line_dump += line[i] + sep[i]
                        line_dump += line[-1]
                        line_dump += "\n"

                fin.write(line_dump)



def generate(config_path: str, output_path: str):
    conf = Configuration(config_path)
    gen = TestcaseGenerator(output_path, conf)
    gen.generate()


CONFIG_PATH = ""
OUTPUT_DIR = ""

if __name__ == "__main__":
    generate(CONFIG_PATH, OUTPUT_DIR)