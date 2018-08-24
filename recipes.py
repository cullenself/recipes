#!/usr/bin/env python3
import yaml
from glob import glob
from os import system
from sys import exit as sys_exit
from clint.textui import prompt, puts, colored, indent, columns
from clint.textui.cols import _find_unix_console_width
from transitions.extensions import HierarchicalMachine as Machine

class RecipeViewer(object):
    # Globals
    states = ['main_menu',{'name':'recipe', 'children':['overview','directions','ingredients','editting'], 'initial':'overview'},'quitting','_init']
    transitions = [
            { 'trigger':'view_recipe', 'source':['main_menu','recipe'], 'dest':'recipe', 'after':'show_recipe' },
            { 'trigger':'view_menu', 'source':'recipe', 'dest':'main_menu', 'after':'show_menu' },
            { 'trigger':'view_ingredients', 'source':'recipe', 'dest':'recipe_ingredients', 'after':'show_ingredients' },
            { 'trigger':'view_directions', 'source':'recipe', 'dest':'recipe_directions', 'after':'show_directions' },
            { 'trigger':'edit', 'source':'recipe', 'dest':'recipe_editting', 'after':'edit_menu' },
            { 'trigger':'quit', 'source':'*', 'dest':'quitting', 'after':'exit', 'before':'clear' },
            { 'trigger':'start', 'source':'_init', 'dest':'main_menu', 'after':'show_menu'}
    ]
    NARROW = 60

    def __init__(self):
        self.machine = Machine(model=self, states=RecipeViewer.states, transitions=self.transitions, initial='_init', auto_transitions=False)
        self.WIDTH = _find_unix_console_width()
        self.LB = ''.center(self.WIDTH,'=')
        self.file = ''
        self.prompt = ''
        self.options = []
        self.start()
        self.RECIPE_OPTIONS = [{'selector': 'I','prompt':'Ingredients','return':self.view_ingredients},
               {'selector': 'D','prompt':'Directions','return':self.view_directions},
               {'selector': 'V','prompt':'Return to Recipe Overview','return':self.view_recipe},
               {'selector': 'E','prompt':'Edit Recipe','return':self.edit},
               {'selector': 'R','prompt':'Return to Main Menu','return':self.view_menu},
               {'selector': 'Q','prompt':'Quit','return':self.quit}]

    def clear(self, *args):
        _ = system('clear') # This isn't portable, but works for me
        return

    def wait(self):
        _ = system('read -s -n 1') # Again not portable
        return

    def exit(*args):
        sys_exit()

    def header(self, text):
        puts(self.LB)
        puts(colored.red(text.center(self.WIDTH)))
        puts(self.LB)
        puts()
        return

    def show_menu(self):
        self.header_text = 'Recipes'
        self.text = ''
        
        files = glob('*.yaml')
        names = [' '.join([s.title() for s in f.split('.')[0].split('_')]) for f in files]
        self.options = []
        for key, opt in enumerate(names):
            self.options.append({'selector':key+1,'prompt':opt,'return':lambda bound_file=files[key]: self.view_recipe(bound_file)})
        self.options.append({'selector':'Q','prompt':'Quit','return':quit})
        self.prompt = 'Choose a recipe'

        return

    def show_recipe(self, file_name=''):
        if file_name!='':
            with open(file_name,'r') as fp:
                self.data = yaml.load(fp)
        self.header_text = self.data['Title']

        tags_text = 'Tags:\n'
        for tag in self.data['Tags']:
            tags_text += ' > ' + str(tag) + '\n'

        notes_text = 'Notes:\n'
        for note in self.data['Notes']:
            notes_text += ' > ' + str(note) + '\n'

        self.text = tags_text + '\n' + notes_text
        self.options = [opt for opt in self.RECIPE_OPTIONS if opt['return'] != self.view_recipe]
        self.prompt = 'View: '
        return

    def show_ingredients(self):
        self.text = self.get_ingr_text()
        self.options = [opt for opt in self.RECIPE_OPTIONS if opt['return'] != self.view_ingredients]
        return

    def get_ingr_text(self):
        text = 'Ingredients:\n'
        max_ingr = max([len(ingr) for ingr, quan in self.data['Ingredients'].items()]) + 1
        for ingr, quan in self.data['Ingredients'].items():
            text += ' > ' + (ingr.ljust(max_ingr) + ": " + str(quan)) + '\n'
        return text

    def show_directions(self):
        peek = lambda x: (lambda v=x.pop(): (lambda t=x.append(v): v)() )() # this is the dumbest line of code I've ever written
        ingr_text = self.get_ingr_text()
        ingr_width = max([len(s) for s in ingr_text.split('\n')]) + 3
        dir_text = 'Directions:\n'
        if self.WIDTH>self.NARROW:
            dir_width = self.WIDTH - ingr_width - 3
            for step, action in self.data['Directions'].items():
                action = str(action).split()
                action.reverse()
                line = ' ' + str(step) + ': '
                while action:
                    while action and len(line+peek(action)) < dir_width:
                        line += action.pop() + ' '
                    dir_text += line + '\n'
                    line = '' 

            self.text = ''
            ingr_text = ingr_text.split('\n')
            dir_text = dir_text.split('\n')
            len_diff = len(ingr_text) - len(dir_text)
            if len_diff > 0:
                dir_text.extend(['']*len_diff)
            if len_diff < 0:
                ingr_text.extend(['']*abs(len_diff))
            for i in range(0,len(ingr_text)):
                self.text += ingr_text[i].ljust(ingr_width) + '   ' + dir_text[i] + '\n'
        else:
            for step, action in self.data['Directions'].items():
                dir_text += ' ' + str(step) + ': ' + str(action) + '\n'
            self.text = ingr_text + '\n' + dir_text

        self.options = [opt for opt in self.RECIPE_OPTIONS if opt['return'] != self.view_directions]
        return

    def edit_menu(self):
        self.text = 'Editting not yet implemented.\n'
        self.options = [opt for opt in self.RECIPE_OPTIONS if opt['return'] != self.edit]
        return

if __name__ == '__main__':
    rv = RecipeViewer()
    while (True):
        rv.clear()
        rv.header(rv.header_text)
        puts(rv.text)
        r = prompt.options(rv.prompt,rv.options)
        r()
