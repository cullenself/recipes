#!/usr/bin/env python3
import yaml
import glob
from os import system
from sys import exit as sys_exit
from clint.textui import prompt, puts, colored, indent, columns
from clint.textui.cols import _find_unix_console_width

# Globals
WIDTH = _find_unix_console_width()
LB = ''.center(WIDTH,'=')
HEADER = LB+'\n'+colored.red('Recipes'.center(WIDTH))+'\n'+LB+'\n'

def clear():
    _ = system('clear') # This isn't portable, but works for me
    return

def wait():
    _ = system('read -s -n 1') # Again not portable
    return

def exit(*args):
    sys_exit()

def header(text):
    puts(LB)
    puts(colored.red(text.center(WIDTH)))
    puts(LB)
    puts()
    return

def main_menu(*args):
    files = glob.glob('*.yaml')
    names = [' '.join([s.title() for s in f.split('.')[0].split('_')]) for f in files]
    main_options = []
    for key, opt in enumerate(names):
        main_options.append({'selector':key+1,'prompt':opt,'return':key})
    main_options.append({'selector':'Q','prompt':'Quit'})

    clear()
    header('Recipes')
    r = prompt.options('Choose a recipe:', main_options)
    if r == 'Q':
        exit()
    else:
        view(files[r])

def view(data):
    if isinstance(data,str):
        file_name = data
        with open(file_name,'r') as fp:
            data = yaml.load(fp)

    clear()
    header(data['Title'])
    puts('Tags')
    with indent(4, quote=' >'):
        for t in data['Tags']:
            puts(t)
    r = list_options(view)
    r(data)

def list_options(current):
    puts()
    current_opts = [opt for opt in OPTIONS if opt['return'] != current]
    r = prompt.options('View:',current_opts)
    return r

def ingredients(data):
    clear()
    header(data['Title'])
    puts('Ingredients')
    with indent(4, quote=' >'):
        max_ingr = max([len(ingr) for ingr, quan in data['Ingredients'].items()]) + 1
        for ingr, quan in data['Ingredients'].items():
            puts(ingr.ljust(max_ingr) + ": " + str(quan))
    r = list_options(ingredients)
    r(data)
    return

def directions(data):
    clear()
    header(data['Title'])
    puts('Directions')
    
    # Print the list of ingredients anyways
    ingr_str = ''
    max_ingr = max([len(ingr) for ingr, quan in data['Ingredients'].items()]) + 1
    max_quan = max([len(str(quan)) for ingr, quan in data['Ingredients'].items()]) + 5
    for ingr, quan in data['Ingredients'].items():
        ingr_str += ingr.ljust(max_ingr) + ": " + str(quan) + '\n'

    dir_str = ''
    for step, action in data['Directions'].items():
        dir_str += str(step) + ": " + action + '\n'

    if WIDTH >= max_ingr+max_quan+40:
        puts(columns([ingr_str, max_ingr + max_quan],[dir_str, WIDTH - max_ingr - max_quan - 5])) # this somehow strips the ljust
    else:
        puts(ingr_str)
        puts(dir_str)
    wait()
    r = list_options(directions)
    r(data)
    return

def notes(data):
    clear()
    header(data['Title'])
    puts('Notes')
    with indent(4, quote=' >'):
        for note in data['Notes']:
            puts(note)
    r = list_options(notes)
    r(data)
    return

OPTIONS = [{'selector': 'I','prompt':'Ingredients','return':ingredients},
           {'selector': 'D','prompt':'Directions','return':directions},
           {'selector': 'N','prompt':'Notes','return':notes},
           {'selector': 'V','prompt':'Return to Recipe Overview','return':view},
           {'selector': 'R','prompt':'Return to Main Menu','return':main_menu},
           {'selector': 'Q','prompt':'Quit','return':exit}]

if __name__ == '__main__':
    main_menu()
