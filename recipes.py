#!/usr/bin/env python3
import yaml
from glob import glob
from os import system
from clint.textui import prompt, puts, colored, indent, columns
from clint.textui.cols import _find_unix_console_width
from transitions.extensions import HierarchicalMachine as Machine
from transitions.core import MachineError
from collections import OrderedDict
from ftplib import FTP
import urwid

class RecipeViewer(object):
    # Globals
    STATES = ['main_menu',{'name':'recipe', 'children':['overview','directions','ingredients','editting'], 'initial':'overview'},'_init']
    TRANSITIONS = [
            { 'trigger':'view_recipe',      'source':['main_menu','recipe'],    'dest':'recipe',        'after':'show_recipe' },
            { 'trigger':'view_menu',        'source':'recipe',          'dest':'main_menu',             'after':'show_menu' },
            { 'trigger':'return_up',        'source':'recipe_overview', 'dest':'main_menu',             'after':'show_menu' },
            { 'trigger':'return_up',        'source':'recipe',          'dest':'recipe_overview',       'after':'show_recipe'},
            { 'trigger':'view_ingredients', 'source':'recipe',          'dest':'recipe_ingredients',    'after':'show_ingredients' },
            { 'trigger':'view_directions',  'source':'recipe',          'dest':'recipe_directions',     'after':'show_directions' },
            { 'trigger':'edit',             'source':'recipe',          'dest':'recipe_editting',       'after':'edit_menu' },
            { 'trigger':'start',            'source':'_init',           'dest':'main_menu',             'after':'build_view'},
            { 'trigger':'print_recipe',     'source':'recipe',          'dest':'=',                     'after':'print_file'},
    ]
    PRINTER = '192.168.0.18'
    PALETTE = [
            ('reversed', 'standout', ''),
            ('header','dark red',''),
            ('quit_button','dark red','white')
    ]

    def __init__(self):
        self.machine = Machine(model=self, states=RecipeViewer.STATES, transitions=RecipeViewer.TRANSITIONS, initial='_init', auto_transitions=False) # initialize the state machine
        self.start() # start state machine
        self.file = '' # current recipe file
        self.loop = urwid.MainLoop(self.top, palette=RecipeViewer.PALETTE, unhandled_input=self.unhandled_input) # initialize Urwid display
        self.loop.run() # and start it

    def unhandled_input(self,key):
        '''Handle key commands
        Relies on state machine throwing exceptions
        about invalid transitions.
        '''
        if key in ('q','Q','f8'):   # Quit
            raise urwid.ExitMainLoop()
        if key in ('i','I'):        # Ingredients
            try:
                self.view_ingredients()
                return True
            except MachineError:
                return False 
        if key in ('r','R'):        # Return
            try:
                self.return_up()
                return True
            except MachineError:
                return False
        if key in ('d','D'):        # Directions
            try:
                self.view_directions()
                return True
            except MachineError:
                return False
        if key in ('e','E'):        # Edit
            try:
                self.edit()
                return True
            except MachineError:
                return False
        if key in ('p','P'):        # Print
            try:
                self.print_recipe()
                return True
            except MachineError:
                return False
        return False
                
    def show_menu(self):
        '''Display the main recipe selection'''
        self.bt.set_text('Recipes')
        files = glob('*.yaml')
        names = [' '.join([s.title() for s in f.split('.')[0].split('_')]) for f in files]
        body = []
        for key, opt in enumerate(names):
            button = urwid.Button(opt)
            button._label.align = 'center'
            urwid.connect_signal(button, 'click', self.view_recipe, files[key])
            body.append(urwid.AttrMap(button, None, focus_map='reversed'))
        self.main.original_widget = urwid.Padding(urwid.ListBox(urwid.SimpleFocusListWalker(body)), left=2, right=2)
        return
 
    def build_view(self):
        '''Set up frame for interface'''
        self.bt = urwid.BigText('Recipes',urwid.font.Thin6x6Font())
        header = urwid.AttrMap(self.bt,'header')
        header = urwid.Padding(header, width='clip', align='center')
        header = urwid.LineBox(header)

        footer = urwid.Text(['Press ', ('quit_button', 'Q'), ' to quit'])
        
        self.main = urwid.Padding(urwid.Text('placeholder'), left=2, right=2)
        #body = urwid.Filler(self.main,height=10,valign='middle',top=1)
        body = urwid.LineBox(self.main)
        #body = urwid.Overlay(body, urwid.SolidFill(u' '), align='center', width=40, valign='middle', height=10)
        self.top = urwid.Frame(body=body,header=header,footer=footer)

        self.show_menu()
        return

    def show_recipe(self, button=None, file_name=''):
        '''Load and display a recipe overview'''
        if file_name!='':
            self.file = file_name
            with open(file_name,'r') as fp:
                self.data = yaml.load(fp)

        self.bt.set_text(self.data['Title'])

        tags = [ urwid.Text('Tags'), urwid.Divider() ]
        for tag in self.data['Tags']:
            tags.append(urwid.Text(' > ' + tag))
        tags_list = urwid.ListBox(urwid.SimpleListWalker(tags))

        notes = [ urwid.Text('Notes'), urwid.Divider() ]
        for note in self.data['Notes']:
            notes.append(urwid.Text(' > ' + note))
        notes_list = urwid.ListBox(urwid.SimpleListWalker(notes))

        self.main.original_widget = urwid.Columns([tags_list,notes_list])
        return

    def print_file(self):
        '''Print the YAML file to networked printer'''
        with FTP(self.PRINTER) as ftp:
            ftp.login()
            with open(self.file,'rb') as fp:
                ftp.storlines('STOR recipe.yaml', fp)
        return

    def show_ingredients(self):
        '''Display list of ingredients'''
        ingr_list = []
        quan_list = []
        for ingr, quan in self.data['Ingredients'].items():
            ingr_list.append(urwid.Text(ingr))
            quan_list.append(urwid.Text(str(quan)))
        ingr_list = urwid.ListBox(urwid.SimpleListWalker(ingr_list))
        quan_list = urwid.ListBox(urwid.SimpleListWalker(quan_list))
        ingr_col = urwid.Columns([ingr_list,quan_list])
        self.main.original_widget = ingr_col
        return

    def show_directions(self):
        '''Show directions and ingredients'''
        ingr_list = []
        quan_list = []
        for ingr, quan in self.data['Ingredients'].items():
            ingr_list.append(urwid.Text(ingr))
            quan_list.append(urwid.Text(str(quan)))
        ingr_list = urwid.ListBox(urwid.SimpleListWalker(ingr_list)) # need to style these so that scrolling is obvious
        quan_list = urwid.ListBox(urwid.SimpleListWalker(quan_list))
        ingr_col = urwid.Columns([ingr_list,quan_list])
        
        inst_list = []
        for step, action in self.data['Directions'].items():
            inst_list.append(urwid.Text(str(step) + ': ' + action))
        inst_list = urwid.ListBox(urwid.SimpleListWalker(inst_list))
        self.main.original_widget = urwid.Pile([ingr_col, inst_list])
        return

    def save(self):
        self.data['Ingredients'] = OrderedDict(self.data['Ingredients']) # yaml likes to put these in sorted order
        with open(self.file,'w') as fp:
            yaml.dump(OrderedDict(self.data), fp, default_flow_style=False, indent=4)
        self.view_recipe()
        return

    def save_tag(self, button):
        '''Read user input and save'''
        self.data['Tags'].append(self.tags_edit.get_edit_text())
        self.save()
        return

    def save_note(self, button):
        '''Read user input and save'''
        self.data['Notes'].append(self.notes_edit.get_edit_text())
        self.save()
        return

    def edit_menu(self):
        '''Build edit menu'''
        tags = [ urwid.Text('Tags'), urwid.Divider() ]
        for tag in self.data['Tags']:
            tags.append(urwid.Text(' > ' + tag))
        tags_list = urwid.ListBox(urwid.SimpleListWalker(tags))
        self.tags_edit = urwid.Edit('Add a Tag:')
        tags_save = urwid.Button('Save Tag', self.save_tag)
        tags_save._label.align = 'center'
        tags_save = urwid.AttrMap(tags_save, None, focus_map='reversed')
        tags_buttons = urwid.ListBox(urwid.SimpleFocusListWalker([self.tags_edit, tags_save]))
        tags_side = urwid.Pile([tags_list, tags_buttons])

        notes = [ urwid.Text('Notes'), urwid.Divider() ] # this code is redundant, probably could pass attribute ('Notes') and label ('Note') into custom Pile generator
        for note in self.data['Notes']:
            notes.append(urwid.Text(' > ' + note))
        notes_list = urwid.ListBox(urwid.SimpleListWalker(notes))
        self.notes_edit = urwid.Edit('Add a Note:')
        notes_save = urwid.Button('Save Note', self.save_tag)
        notes_save._label.align = 'center'
        notes_save = urwid.AttrMap(notes_save, None, focus_map='reversed')
        notes_buttons = urwid.ListBox(urwid.SimpleFocusListWalker([self.notes_edit, notes_save]))
        notes_side = urwid.Pile([notes_list, notes_buttons])
    
        self.main.original_widget = urwid.Columns([tags_side, notes_side])
        return

def represent_ordereddict(dumper, data):
    '''Helper function for YAML to dump OrderedDicts'''
    value = []
    for item_key, item_value in data.items():
        node_key = dumper.represent_data(item_key)
        node_value = dumper.represent_data(item_value)
        value.append((node_key, node_value))
    return yaml.nodes.MappingNode(u'tag:yaml.org,2002:map', value)

if __name__ == '__main__':
    yaml.add_representer(OrderedDict, represent_ordereddict)
    RecipeViewer()
