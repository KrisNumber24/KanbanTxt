# KanbanTxt - A light todo.txt editor that display the to do list as a kanban board.
# Copyright (C) 2022  KrisNumber24

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  
# If not, see https://github.com/KrisNumber24/KanbanTxt/blob/main/LICENSE.

import os
import re
from datetime import date
import tkinter as tk
from tkinter import filedialog
import tkinter.font as tkFont
import argparse

class KanbanTxtViewer:

    THEMES = {
        'LIGHT_COLORS' : {
            "To Do": '#f27272',
            "In progress": '#00b6e4',
            "Validation": '#22b57f',
            "Done": "#8BC34A",
            "To Do-column": '#daecf1',
            "In progress-column": '#daecf1',
            "Validation-column": '#daecf1',
            "Done-column": "#daecf1",
            "important": "#a7083b",
            "project": '#00b6e4',
            'context': '#1c9c6d',
            'main-background': "#ffffff",
            'card-background': '#ffffff',
            'done-card-background': '#edf5f7',
            'editor-background': '#cae1e8',
            'main-text': '#4c6066',
            'editor-text': '#000000',
            'button': '#415358',
        },

        'DARK_COLORS' : {
            "To Do": '#f27272',
            "In progress": '#00b6e4',
            "Validation": '#22b57f',
            "Done": "#8BC34A",
            "To Do-column": '#15151f',
            "In progress-column": '#15151f',
            "Validation-column": '#15151f',
            "Done-column": "#15151f",
            "important": "#e12360",
            "project": '#00b6e4',
            'context': '#1c9c6d',
            'main-background': "#1f1f2b",
            'card-background': '#2c2c3a',
            'done-card-background': '#1f1f2b',
            'editor-background': '#15151f',
            'main-text': '#b6cbd1',
            'editor-text': '#cee4eb',
            'button': '#b6cbd1',
        },
    }

    FONTS = []

    class TaggedTaskList:
        '''
        An object that manage a list of tags and stores tasks that have specific
        tags. It has a listbox attached to it so this widget is updated when a new
        tag is found or it is needed to reset the tags list.
        '''
        attached_listBox = None
        tags = []
        tagged_tasks = {}

        def __init__(self, listBox) -> None:
            self.attached_listBox = listBox

        def create_tag(self, name):
            if not name in self.tags:
                self.tags.append(name)
                self.tagged_tasks[name] = []
                self.attached_listBox.insert(tk.END, name)
        
        def push_back_task(self, tag, task_widget):
            self.create_tag(tag)
            self.tagged_tasks[tag].append(task_widget)
        
        def clear(self):
            self.tags.clear()
            self.tagged_tasks.clear()
            self.attached_listBox.delete(0, tk.END)
    
    project_tasks = None


    win_height = 0
    win_width = 0

    is_filters_visible = False 

    def __init__(self, file='', darkmode=False) -> None:
        self.darkmode = darkmode

        self.file = file

        self.current_date = date.today()
        
        self.ui_columns = {
            "To Do": [],
            "In progress": [],
            "Validation": [],
            "Done": []
        }

        self._after_id = -1
        
        self.draw_ui(1000, 500, 0, 0)

        
    def draw_ui(self, window_width, window_height, window_x, window_y):
        # Define theme
        dark_option = 'LIGHT_COLORS'
        if self.darkmode: 
            dark_option = 'DARK_COLORS'

        default_scheme = list(self.THEMES.keys())[0]
        color_scheme = self.THEMES.get(dark_option, default_scheme)

        self.COLORS = color_scheme

        # Create main window
        self.main_window = tk.Tk()
        self.main_window.title('KanbanTxt')
        self.main_window['background'] = self.COLORS['main-background']
        self.main_window['relief'] = 'flat'
        self.main_window.geometry("%dx%d+%d+%d" % (window_width, window_height, window_x, window_y))

        self.FONTS.append(tkFont.Font(name='main', family='arial', size=10, weight=tkFont.NORMAL))
        self.FONTS.append(tkFont.Font(name='h2', family='arial', size=14, weight=tkFont.NORMAL))
        self.FONTS.append(tkFont.Font(name='done-task', family='arial', size='10', overstrike=1))

        # Bind shortkey to open or save a new file
        self.main_window.bind('<Control-s>', self.reload_and_create_file)
        self.main_window.bind('<Control-o>', self.open_file)

        self.draw_editor_panel()

        self.draw_content_frame()

        # Load the file provided in arguments if there is one
        if os.path.isfile(self.file):
            self.load_file()


    def draw_editor_panel(self):
        # EDITION FRAME
        edition_frame = tk.Frame(self.main_window, bg=self.COLORS['editor-background'], width=20)
        edition_frame.grid(row=0, column=0, sticky=tk.NSEW)
        self.main_window.grid_rowconfigure(0, weight=1)
        self.main_window.grid_columnconfigure(0, weight=1)
        
        # HEADER
        editor_header = tk.Frame(edition_frame, bg=self.COLORS['editor-background'])
        editor_header.pack(side='top', fill='both', expand=0, padx=10, pady=0)
        
        save_button = self.create_button(
            editor_header,
            text="Save",
            bordersize=2,
            color=self.COLORS['button'],
            activetextcolor=self.COLORS['main-background'],
            command=self.reload_and_create_file
        )
        save_button.pack(side="right", padx=(10,0), pady=10, anchor=tk.NE)
        
        load_button = self.create_button(
            editor_header,
            text="Load",
            bordersize=2,
            color=self.COLORS['button'],
            activetextcolor=self.COLORS['main-background'],
            command=self.open_file
        )
        load_button.pack(side="right", padx=(10,0), pady=10, anchor=tk.NE)

        # Light mode / dark mode switch
        button_color = self.COLORS['button']

        darkmode_button_border = tk.Frame(
            editor_header,
            bg=button_color
        )
        darkmode_button_border.pack(side="left", padx=(10,0), pady=10, anchor=tk.NE)
        darkmode_button = tk.Label(
            darkmode_button_border, 
            text='🔆', 
            relief='flat', 
            bg=self.COLORS['editor-background'], 
            fg=button_color,
            font=('arial', 12))
        darkmode_button.pack(side="left", padx=2, pady=2)
        darkmode_button.bind("<Button-1>", self.switch_darkmode)

        darkmode_button = tk.Label(
            darkmode_button_border, 
            text='🌙', 
            relief='flat', 
            bg=button_color, 
            fg=self.COLORS['editor-background'],
            font=('arial', 12))
        darkmode_button.pack(side="left", padx=2, pady=2)
        darkmode_button.bind("<Button-1>", self.switch_darkmode)
        # END Light mode / dark mode switch

        #END HEADER

        # Separator
        tk.Frame(edition_frame, height=1, bg=self.COLORS['main-text']).pack(side='top', fill='x')

        # MEMO
        cheat_sheet = tk.Label(edition_frame, text='------ Memo ------\n'
            '(A) :  in progress\n'
            '(B) :  important todo\n'
            '(C) :  validation\n'
            'Ctrl + s :  refresh and save\n'
            'Alt + ↑ / ↓ :  move line up / down\n', 
            bg=self.COLORS['editor-background'], 
            anchor=tk.NW, 
            justify='left', 
            fg=self.COLORS['main-text'], 
            font=tkFont.nametofont('main'),
        )
        cheat_sheet.pack(side="top", fill="x", padx=10)
        # MEMO END

        # Separator
        tk.Frame(
            edition_frame, height=1, bg=self.COLORS['main-text']).pack(side='top', fill='x')
        
        # EDITOR
        self.text_editor = tk.Text(
            edition_frame, 
            bg=self.COLORS['editor-background'], 
            insertbackground=self.COLORS['editor-text'], 
            fg=self.COLORS['editor-text'], 
            relief="flat", 
            width=40,
            height=10,
            maxundo=10,
            undo=True,
            wrap=tk.WORD,
            spacing1=10,
            spacing3=10,
            insertwidth=3,
        )
        self.text_editor.pack(side="top", fill="both", expand=1, padx=10, pady=10)
        self.text_editor.tag_configure('pair', background=self.COLORS['done-card-background'])
        self.text_editor.tag_configure('insert', background='red')

        # EDITOR TOOLBAR
        editor_toolbar = tk.Frame(edition_frame, bg=self.COLORS['editor-background'])
        editor_toolbar.pack(side='top', padx=10, pady=10, fill='both')

        # Move to todo
        self.create_button(
            editor_toolbar, 
            '✅→⚫', 
            self.COLORS['To Do'], 
            command=self.move_to_todo
        ).grid(row=0, sticky='ew', column=0, padx=5, pady=5)

        # Set as important
        self.create_button(
            editor_toolbar, 
            '✅→⚫', 
            self.COLORS['important'], 
            command=self.move_to_important
        ).grid(row=0, sticky='ew', column=1, padx=5, pady=5)

        # Move to In progress
        self.create_button(
            editor_toolbar, 
            '✅→⚫', 
            self.COLORS['In progress'], 
            command=self.move_to_in_progress
        ).grid(row=0, sticky='ew', column=2, padx=5, pady=5)

        # Move to Validation
        self.create_button(
            editor_toolbar, 
            '✅→⚫', 
            self.COLORS['Validation'], 
            command=self.move_to_validation
        ).grid(row=0, sticky='ew', column=3, padx=5, pady=5)

        # Move to Done
        self.create_button(
            editor_toolbar, 
            '✅→⚫', 
            self.COLORS['Done'], 
            command=self.move_to_done
        ).grid(row=0, sticky='ew', column=4, padx=5, pady=5)

        # Move line up
        self.create_button(
            editor_toolbar, 
            '+ date', 
            self.COLORS['button'], 
            command=self.add_date
        ).grid(row=1, sticky='ew', column=0, padx=5, pady=5)

        # Move line up
        self.create_button(
            editor_toolbar, 
            '↑', 
            self.COLORS['button'], 
            command=self.move_line_up
        ).grid(row=1, sticky='ew', column=1, padx=5, pady=5)

        # Move line down
        self.create_button(
            editor_toolbar, 
            '↓', 
            self.COLORS['button'], 
            command=self.move_line_down
        ).grid(row=1, sticky='ew', column=2, padx=5, pady=5)

        # Delete line
        self.create_button(
            editor_toolbar, 
            'Delete', 
            self.COLORS['button'], 
            command=self.remove_line
        ).grid(row=1, sticky='ew', column=3, padx=5, pady=5)

        editor_toolbar.columnconfigure(0, weight=1, uniform='toolbar-item')
        editor_toolbar.columnconfigure(1, weight=1, uniform='toolbar-item')
        editor_toolbar.columnconfigure(2, weight=1, uniform='toolbar-item')
        editor_toolbar.columnconfigure(3, weight=1, uniform='toolbar-item')
        editor_toolbar.columnconfigure(4, weight=1, uniform='toolbar-item')
        # EDITOR TOOLBAR END

        #EDITOR END

        # Bind all the option to update and save the file
        self.text_editor.bind('<Return>', self.return_pressed)
        self.text_editor.bind('<BackSpace>', self.return_pressed)
        self.text_editor.bind('<Control-space>', self.reload_and_save)
        self.text_editor.bind('<F5>', self.reload_and_save)

        # Shortkeys
        self.text_editor.bind('<Alt-Up>', self.move_line_up)
        self.text_editor.bind('<Alt-Down>', self.move_line_down)
        self.text_editor.bind('<Control-Key-1>', self.move_to_todo)
        self.text_editor.bind('<Control-Key-2>', self.move_to_important)
        self.text_editor.bind('<Control-Key-3>', self.move_to_in_progress)
        self.text_editor.bind('<Control-Key-4>', self.move_to_validation)
        self.text_editor.bind('<Control-Key-5>', self.move_to_done)
    

    def draw_content_frame(self):
        # Create content view that will display kanban
        self.content_frame = tk.Frame(self.main_window, bg=self.COLORS['main-background'])
        self.content_frame.grid(row=0, column=1, sticky=tk.NSEW, padx=10, pady=10)
        
        # Give more space to the kanban view
        self.main_window.grid_columnconfigure(1, weight=6)

        
        # SCROLLABLE CANVAS
        self.scrollable_frame = tk.Frame(self.content_frame, bg=self.COLORS['main-background'])

        scrollbar = tk.Scrollbar(
            self.scrollable_frame, 
            orient="vertical", 
        )
        scrollbar.grid(column=1, row=0, sticky='ns')

        # Use canvas to make content view scrollable
        self.content_canvas = tk.Canvas(
            self.scrollable_frame, 
            bg=self.COLORS['main-background'], 
            bd=0, 
            highlightthickness=0, 
            relief=tk.FLAT
        )
        self.content_canvas.grid(column=0, row=0, sticky='nsew')

        # The frame inside the canvas. It manage the widget displayed inside the canvas
        self.canvas_frame = tk.Frame(self.scrollable_frame, bg=self.COLORS['main-background'])

        # Frame containing the kanban
        self.kanban_frame = tk.Frame(self.canvas_frame, bg=self.COLORS['main-background'])
        self.kanban_frame.pack(fill='x')

        self.canvas_frame_id = self.content_canvas.create_window(
            (0, 0), window=self.canvas_frame, anchor="nw")

        # Attach the scroll bar position to the visible region of the canvas
        self.scrollable_frame.grid_rowconfigure(0, weight=1)
        self.scrollable_frame.grid_columnconfigure(0, weight=1)
        scrollbar.configure(command=self.content_canvas.yview)
        self.content_canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas_frame.configure()

        # END SCROLLABLE CANVAS


        # Prepare filters panel
        self.filters_section = tk.Frame(
            self.content_frame, 
            bg=self.COLORS['main-background'], 
            highlightbackground=self.COLORS['To Do-column'], 
            highlightthickness=2,
            highlightcolor=self.COLORS['To Do-column'],
        )
        self.filters_section.columnconfigure(0, weight=1)
        #self.filters_panel.columnconfigure(1, weight=1)

        filters_title = tk.Label(
            self.filters_section, 
            text="Filters", 
            font=tkFont.nametofont('h2'),
            fg=self.COLORS['main-text'],
            bg=self.COLORS['main-background'],
            anchor=tk.W
        )
        filters_title.grid(column=0, row=0, sticky=tk.EW, padx=10)

        self.toggle_filters_button = tk.Button(
            filters_title, 
            text='▼', 
            fg=self.COLORS['main-text'],
            bg=self.COLORS['main-background'],
            relief='flat',
            borderwidth=0,
            highlightthickness=0,
            activebackground=self.COLORS['done-card-background'],
            activeforeground=self.COLORS['main-text'],
            font=tkFont.nametofont('main'),
            command=self.on_toggle_filters_button_pressed
            )
        self.toggle_filters_button.pack(side='right', padx=5, pady=5)

        self.filters_lists_frame = tk.Frame(
            self.filters_section,
            bg=self.COLORS['main-background']
        )

        # prepare space for the filters list and hide it
        self.filters_lists_frame.grid(column=0, row=1) 
        self.filters_lists_frame.grid_remove()
        
        project_filters_title = tk.Label(
            self.filters_lists_frame,
            font=tkFont.nametofont("main"),
            fg=self.COLORS['project'],
            bg=self.COLORS['main-background'],
            text="+projects"
        )
        project_filters_title.grid(column=0, row=0)

        self.project_filters_list = tk.Listbox(
            self.filters_lists_frame,
            bg=self.COLORS['done-card-background'],
            fg=self.COLORS['main-text'],
            font=tkFont.nametofont('main'),
            selectmode='multiple',
            selectbackground=self.COLORS['project'],
            selectforeground=self.COLORS['main-background'],
            selectborderwidth=0,
            border=0,
            highlightthickness=0
        )
        self.project_filters_list.grid(
            column=0, row=1, pady=5
        )
        self.project_tasks = self.TaggedTaskList(self.project_filters_list)

        self.project_filters_list.bind('<<ListboxSelect>>', self.on_project_filters_selected)

        # Prepare progress bars and kanban itself
        self.progress_bar = tk.Frame(self.content_frame, height=15, bg=self.COLORS['done-card-background'])
        self.progress_bar.pack(side='top', fill='x', padx=10, pady=10)
        self.progress_bars = {}

        self.filters_section.pack(fill='x', padx=10, pady=10)

        # scrollable frame is packed here to be under the progress bar 
        self.scrollable_frame.pack(fill='both', expand=True)

        # position of the current sub progress bar
        sub_bar_pos = 0
        # number of the current column in the tkinter grid
        column_number = 0

        # Create each column and its associated progress bar
        for key, column in self.ui_columns.items():
            column_color = self.COLORS[key + '-column']

            # Create the kanban column
            ui_column = tk.Frame(self.kanban_frame, bg=column_color)
            ui_column.grid(
                row=1, column=column_number, padx=10, pady=0, sticky='nwe')
            self.kanban_frame.grid_columnconfigure(
                column_number, weight=1, uniform="kanban")
            
            top_border = tk.Frame(
                ui_column, 
                bg=self.COLORS[key], 
                height=8
            )
            top_border.pack(fill='x', side="top", anchor=tk.W)

            title_color = self.COLORS[key]
            if title_color == self.COLORS[key + '-column']:
                title_color = self.COLORS['main-background']
            label = tk.Label(
                ui_column, 
                text=key, 
                fg=title_color, 
                bg=ui_column['bg'], 
                anchor=tk.W, 
                font=tkFont.nametofont('h2')
            )
            label.pack(padx=10, pady=(3, 10), fill='x', side="top", anchor=tk.W)

            ui_column_content = tk.Frame(ui_column, bg=ui_column['bg'], height=0)
            ui_column_content.pack(side='top', padx=10, pady=(0,10), fill='x')

            self.ui_columns[key] = ui_column
            self.ui_columns[key].content = ui_column_content

            
            # Create the progress bar associated to the column
            self.progress_bars[key] = {}
            self.progress_bars[key]['bar'] = tk.Frame(
                self.progress_bar, bg=self.COLORS[key])
            self.progress_bars[key]['bar'].place(
                relx=sub_bar_pos, relwidth=0.25, relheight=1)
            
            # Add a label in the progress bar that display the number of tasks
            # in the column
            bar_label_text = key + ': -'
            self.progress_bars[key]['label'] = tk.Label(
                self.progress_bars[key]['bar'], 
                text=bar_label_text, 
                fg=self.COLORS['main-background'], 
                bg=self.progress_bars[key]['bar']['bg'], 
                font=('Arial', 8))
            self.progress_bars[key]['label'].pack(side='left', padx=5)
            
            sub_bar_pos += 0.25
            column_number += 1

        # Bind signals
        #self.content_canvas.bind('<Configure>', self.adapt_canvas_to_window)

        # Allow to bind the mousewheel event to the canvas and scroll through it
        # with the wheel
        self.kanban_frame.bind('<Enter>', self.bind_to_mousewheel)
        self.kanban_frame.bind('<Leave>', self.unbind_to_mousewheel)

        # Move the scroll region according to the scroll
        self.content_frame.bind(
            "<Configure>",
            lambda e: self.content_canvas.configure(
                scrollregion=self.content_canvas.bbox("all")
            )
        )

        # resize kanban frame when window is resied
        self.content_canvas.bind('<Configure>', self.on_window_resize)
    

    def create_button(
        self,
        parent, 
        text="button",
        color="black", 
        activetextcolor="white", 
        bordersize=2,
        command=None
    ):
        """Create a button with a border and no background"""
        button_frame = tk.Frame(
            parent,
            bg=color
        )
        button = tk.Button(
            button_frame, 
            text=text, 
            relief='flat', 
            bg=parent['bg'], 
            fg=color,
            activebackground=color,
            activeforeground=activetextcolor,
            borderwidth=0,
            font=tkFont.nametofont('main'),
            command=command)
        button.pack(padx=bordersize, pady=bordersize, fill='both')

        return button_frame


    def fread(self, filename):
        """Read file and close the file."""
        with open(filename, 'r', encoding='utf8') as f:
            return f.read()

    def fwrite(self, filename, text):
        """Write content to file and close the file."""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(text)

    def parse_todo_txt(self, p_todo_txt):
        """Parse a todo txt content and return data as a dictionary"""
        tasks = {
            "To Do": [],
            "In progress": [],
            "Validation": [],
            "Done": []
        }

        important_tasks = []

        # reset the task lists filtered by projects
        self.project_tasks.clear()

        # Erase the columns content
        for ui_column_name, ui_column in self.ui_columns.items():
            ui_column.content.pack_forget()
            for widget in ui_column.content.winfo_children():
                widget.destroy()

        important_frame = tk.Frame(self.ui_columns['To Do'].content, bg=ui_column.content['bg'])    
        important_frame.pack(side='top', fill='x')

        todo_list = p_todo_txt.split("\n")

        for index, task in enumerate(todo_list):
            if len(task) != 0:
                task_data = re.match(
                    r'^(?P<isDone>x )? '
                    r'?(?P<priority>\([A-Z]\))? '
                    r'?(?P<dates>\d\d\d\d-\d\d-\d\d( \d\d\d\d-\d\d-\d\d)?)? '
                    r'?(?P<subject>[^@\+]+) ?' 
                    r'?(?P<project>\+[^@\s]+)? '
                    r'?(?P<context>@\S+)?',
                    task)
                
                task = task_data.groupdict()
                task['is_important'] = False

                category = "To Do"

                if task.get("isDone"):
                    category = "Done"
                
                elif task.get("priority"):
                    priority = task['priority']

                    if priority == "(B)":
                        task['is_important'] = True

                    elif priority == "(A)":
                        category ='In progress'
                    
                    elif priority == "(C)":
                        category = 'Validation'

                if task['is_important']:
                    important_tasks.append(task)
                else: 
                    tasks[category].append(task)
                
                start_date = None
                end_date = None
                if task.get('dates'):
                    dates = []
                    dates = task.get('dates').split(' ')
                    if len(dates) == 1:
                        start_date = date.fromisoformat(dates[0])
                    elif len(dates) == 2:
                        start_date = date.fromisoformat(dates[1])
                        end_date = date.fromisoformat(dates[0])
                    

                card_bg = self.COLORS['card-background']
                font = 'main'
                if category == 'Done':
                    card_bg = self.COLORS['done-card-background']
                    font = 'done-task'

                card_parent = self.ui_columns[category].content
                if task.get('is_important', False):
                    card_parent = important_frame

                task_card = self.draw_card(
                    card_parent,
                    task.get('subject', '???'),
                    card_bg,
                    font,
                    is_important=task['is_important'],
                    project=task.get('project'), 
                    context=task.get('context'),
                    start_date=start_date,
                    end_date=end_date,
                    state=category,
                    name="task#" + str(index + 1)
                )

                # register the task in the projects dictionary
                if task.get('project'):
                    project = task.get('project')

                    self.project_tasks.push_back_task(project, task_card)
                
                else:
                    self.project_tasks.push_back_task(None, task_card)

        tasks['To Do'] = important_tasks + tasks['To Do']

        # Compute proportion for each column tasks and update progress bars
        tasks_number = {
            'To Do': len(tasks["To Do"]),
            'In progress': len(tasks['In progress']),
            'Validation': len(tasks['Validation']),
            'Done': len(tasks['Done'])
        }
        total_tasks = 0

        for key, number in tasks_number.items():
            total_tasks += number

        if total_tasks > 0:
            percentages = {
                'To Do': tasks_number['To Do'] / total_tasks,
                'In progress': tasks_number['In progress'] / total_tasks,
                'Validation': tasks_number['Validation'] / total_tasks,
                'Done': tasks_number['Done'] / total_tasks
            }

            bar_x = 0

            for key, progress_bar in self.progress_bars.items():
                progress_bar['bar'].place(relx=bar_x, relwidth=percentages[key], relheight=1)
                label_text = key + ': ' + str(tasks_number[key])
                progress_bar['label'].config(text=label_text)
                bar_x += percentages[key]

        for ui_column_name, ui_column in self.ui_columns.items():
            tmp_frame = tk.Frame(ui_column.content, width=0, height=0)
            tmp_frame.pack()
            ui_column.content.update()
            tmp_frame.destroy()
            ui_column.content.pack(side='top', padx=10, pady=(0,10), fill='x')
        
        self.update_editor_line_colors()

        self.main_window.update()

        return tasks


    def draw_card(
        self, 
        parent, 
        subject, 
        bg, 
        font='main', 
        is_important=False, 
        project=None, 
        context=None, 
        start_date=None,
        end_date=None,
        state='To Do',
        name=""
    ):
        # Create the card frame
        ui_card = tk.Frame(parent, bg=bg, height=200)

        subject_padx = 10

        # If needed add a red border and an asterisk on important card
        if is_important: 
            important_border = tk.Frame(ui_card, bg=self.COLORS["important"], width="3")
            important_border.pack(side="left", fill='y')
            important_label = tk.Label(
                ui_card, 
                text="*", 
                fg=self.COLORS["important"], 
                bg=ui_card['bg'], 
                anchor=tk.W, 
                font=tkFont.Font(family='arial', size=18, weight=tkFont.BOLD)
            )
            important_label.pack(side="left", anchor=tk.NW, padx=0, pady=(5,0))
            subject_padx = 0

        # Subject label
        # If a name were given, used it as id
        if len(name) == 0:
            name= None

        card_label = tk.Label(
            ui_card, 
            text=subject, 
            fg=self.COLORS['main-text'], 
            bg=ui_card['bg'], 
            anchor=tk.W, 
            wraplength=200, 
            justify='left',
            font=tkFont.nametofont(font),
            cursor='hand2',
            name=name
        )
        
        # Adapt elide length when width change
        card_label.bind("<Configure>", self.on_card_width_changed)
        card_label.pack(padx=subject_padx, pady=5, fill='x', side="top", anchor=tk.W)

        # If needed show the task duration
        if start_date:
            duration = 0
            if not end_date:
                end_date = self.current_date

            duration = end_date.toordinal() - start_date.toordinal()
            duration_string = "%d days: \n" % (duration)
            for i in range(duration):
                duration_string += "🔘"

            duration_label = tk.Label(
                ui_card, 
                text = duration_string,
                fg=self.COLORS[state], 
                bg=ui_card['bg'], 
                anchor=tk.W, 
                justify='left',
                font=("Arial", 8),
                wraplength=85, 

            )
            if project or context:
                duration_label.pack(side="top", anchor=tk.NW, padx=10, pady=0)
            else:
                duration_label.pack(side="top", anchor=tk.NW, padx=10, pady=(0,10))

        # Add project and context tags if needed
        if project:
            project_label = tk.Label(
                ui_card, 
                text=project, 
                fg=self.COLORS["project"], 
                bg=ui_card['bg'], 
                anchor=tk.E
            )
            project_label.pack(padx=10, pady=5, fill='x', side="top", anchor=tk.E)
        
        if context:
            context_label = tk.Label(
                ui_card, 
                text=context, 
                fg=self.COLORS['context'], 
                bg=ui_card['bg'], 
                anchor=tk.E
            )
            context_label.pack(padx=10, pady=5, fill='x', side="top", anchor=tk.E)

        card_label.bind('<Button-1>', self.highlight_task)

        ui_card.pack(padx=0, pady=(0, 10), side="top", fill='x', expand=1, anchor=tk.NW)

        return ui_card


    def open_file(self, event=None):
        """Open a dialog to select a file to load"""
        self.file = filedialog.askopenfilename(
            initialdir='.', 
            filetypes=[("todo list file", "*todo.txt")],
            title='Choose a todo list to display')
        
        self.load_file()


    def load_file(self):
        if os.path.isfile(self.file):
            todo_txt = self.fread(self.file)
            self.text_editor.delete('1.0', 'end')
            self.text_editor.insert(tk.INSERT, todo_txt)
            self.text_editor.focus()
            self.text_editor.mark_set('insert', 'end')
            self.text_editor.see('insert')
            todo_cards = self.parse_todo_txt(todo_txt)
            # self.update_ui(todo_cards)


    def reload_and_save(self, event=None):
        """Reload the kanban and save the editor content in the current todo.txt
            file """
        data = self.parse_todo_txt(self.text_editor.get("1.0", "end-1c"))
        # self.update_ui(data)
        if self.file:
            self.fwrite(self.file, self.text_editor.get("1.0", "end-1c"))


    def reload_and_create_file(self, event=None):
        """In case no file were open, open a dialog to choose where to save the 
            current data"""
        if not os.path.isfile(self.file):
            new_file = filedialog.asksaveasfile(
                initialdir='.',
                defaultextension='.todo.txt',
                title='Choose a location to save your todo list',
                confirmoverwrite=True,
                filetypes=[('todo list file', '*todo.txt')])
            
            if not new_file:
                return

            # just create the file
            self.file = new_file.name
            new_file.close()
            
            # as tk does'nt support double extensions, we have to write it here
            file_path, extension = os.path.splitext(self.file)
            if extension != 'todo.txt':
                os.rename(self.file, file_path + '.todo.txt')
                self.file = file_path + '.todo.txt'
        
        self.reload_and_save()


    # BINDING CALLBACKS

    def adapt_canvas_to_window(self, event):
        """Resize canvas when window is resized"""
        canvas_width = event.width
        self.content_canvas.itemconfig(self.canvas_frame, width = canvas_width)
                
    def hide_content(self):
        # self.progress_bar.pack_forget()
        # self.kanban_frame.pack_forget()
        pass


    def display_content(self):
        # self.progress_bar.pack(side='top', fill='x', padx=10, pady=10)
        # self.kanban_frame.pack(fill='both')
        pass


    def on_card_width_changed(self, event):
        """Adapt todo cards text wrapping when the window is resized"""
        event.widget['wraplength'] = event.width - 20
    

    def bind_to_mousewheel(self, event):
        """Allow scroll event while pointing the kanban frame"""
        # with Windows OS
        event.widget.bind_all("<MouseWheel>", self.scroll)
        # with Linux OS
        event.widget.bind_all("<Button-4>", self.scroll)
        event.widget.bind_all("<Button-5>", self.scroll)
    

    def unbind_to_mousewheel(self, event):
        """Disable scroll event while not pointing the kanban frame"""
        # with Windows OS
        event.widget.unbind_all("<MouseWheel>")
        # with Linux OS
        event.widget.unbind_all("<Button-4>")
        event.widget.unbind_all("<Button-5>")


    def scroll(self, event):
        """Scroll through the kanban frame"""
        if self.content_canvas.winfo_height() > self.canvas_frame.winfo_height():
            return

        self.content_canvas.yview_scroll(int(-1*(event.delta/120)), "units")


    def switch_darkmode(self, event):
        """Switch from light and dark mode, destroy the UI and recreate it to
            apply the modification"""
        self.darkmode = not self.darkmode
        
        window_geometry = self.main_window.geometry()
        width, height, x, y = re.split("x|\+", window_geometry)

        self.main_window.destroy()
        self.draw_ui(int(width), int(height), int(x), int(y))


    def move_line_up(self, event=None):
        current_line = self.text_editor.get("insert linestart", "insert lineend")
        self.text_editor.delete("insert linestart", "insert lineend + 1c")
        self.text_editor.insert("insert linestart -1l", current_line + '\n')
        if event:
            self.text_editor.mark_set('insert', 'insert linestart -1l')
        else:
            self.text_editor.mark_set('insert', 'insert linestart -2l')
        
        self.update_editor_line_colors()
        #self.reload_and_save()
    

    def move_line_down(self, event=None):
        current_line = self.text_editor.get("insert linestart", "insert lineend")
        self.text_editor.delete("insert linestart", "insert lineend + 1c")
        self.text_editor.insert("insert linestart +1l", current_line + '\n')
        if event:
            self.text_editor.mark_set('insert', 'insert lineend')
        else:
            self.text_editor.mark_set('insert', 'insert lineend +1l')
        
        self.update_editor_line_colors()
        # self.reload_and_save()
    

    def remove_line(self, event=None):
        self.text_editor.delete("insert linestart", "insert lineend + 1c")


    def set_state(self, task, newState):
        task = re.sub(r'^\([A-Z]\) ', '', task)
        task = re.sub(r'^x ', '', task)
        task = re.sub(r'^ ', '', task)
        task = newState + ' ' + task
        return task
    

    def set_editor_line_state(self, new_state):
        current_line = self.text_editor.get("insert linestart", "insert lineend")
        current_line = self.set_state(current_line, new_state)
        self.text_editor.delete("insert linestart", "insert lineend + 1c")
        self.text_editor.insert("insert linestart", current_line + '\n')
        self.text_editor.mark_set('insert', 'insert linestart -1l')
        self.reload_and_save()


    def move_to_todo(self, event=None):
        self.set_editor_line_state('')
    
    def move_to_important(self, event=None):
        self.set_editor_line_state('(B)')
    
    def move_to_in_progress(self, event=None):
        self.set_editor_line_state('(A)')

    def move_to_validation(self, event=None):
        self.set_editor_line_state('(C)')
    
    def move_to_done(self, event=None):
        self.set_editor_line_state('x')

    def add_date(self, event=None):
        current_line = self.text_editor.get("insert linestart", "insert lineend")
        match = re.match(r'x|\([A-C]\) ', current_line)
        insert_index = 0
        if match:
            insert_index = match.end()
        
        self.text_editor.insert("insert linestart +%dc" % (insert_index), str(self.current_date) + " ")
    

    def on_window_resize(self, event):
        if self.win_width == event.width and self.win_height == event.height:
            return

        self.win_width = event.width
        self.win_height = event.height

        self.hide_content()
        
        if self._after_id:
            self.main_window.after_cancel(self._after_id)
        
        self._after_id = self.main_window.after(100, self.update_canvas, event)



    def update_canvas(self, event):
        self.content_canvas.itemconfig(self.canvas_frame_id, width = event.width)

        if event.width < 700:
            index = 1
            for column_name, column in self.ui_columns.items():
                column.grid(
                    row=index, column=0, pady=10, sticky='nwe', columnspan=4)
                index += 1
            
        else:
            index = 0
            for column_name, column in self.ui_columns.items():
                column.grid(
                    row=1, column=index, padx=10, sticky='nwe', columnspan=1)
                index += 1

        self.display_content()
        pass


    def return_pressed(self, event=None):
        self.main_window.after(100, self.update_editor_line_colors)


    def update_editor_line_colors(self, event=None):
        nb_line = int(self.text_editor.index('end-1c').split('.')[0])

        for line_idx in range(nb_line):
            self.text_editor.tag_remove('pair', str(line_idx) + '.0', str(line_idx) + '.0 lineend +1c')
            if line_idx % 2 == 0:
                self.text_editor.tag_add('pair', str(line_idx) + '.0', str(line_idx) + '.0 lineend +1c')
    

    def highlight_task(self, event):
        searched_task_line = event.widget.winfo_name().replace("task#", "")
        self.text_editor.mark_set('insert', searched_task_line + ".0")
        self.text_editor.see('insert')
    

    def on_project_filters_selected(self, event):
        selected_idx = event.widget.curselection()

        if len(selected_idx) == 0:
            selected_idx = range(0, len(self.project_tasks.tags))

        selected_projects = []
        for i in selected_idx:
            selected_projects.append(event.widget.get(i))
        
        widgets_to_hide = []
        widgets_to_show = []

        for key, tasks in self.project_tasks.tagged_tasks.items():
            if not key in selected_projects:
                widgets_to_hide += tasks
            else:
                widgets_to_show += tasks
        
        for widget in widgets_to_hide:
            widget.pack_forget()
        
        for widget in widgets_to_show:
            widget.pack(padx=0, pady=(0, 10), side="top", fill='x', expand=1, anchor=tk.NW)

    
    def on_toggle_filters_button_pressed(self):
        if self.is_filters_visible:
            self.filters_lists_frame.grid_remove()
            self.is_filters_visible = False
            self.toggle_filters_button.configure(text='▼')
        else:
            self.filters_lists_frame.grid()
            self.is_filters_visible = True
            self.toggle_filters_button.configure(text='▲')

def main(args):
    app = KanbanTxtViewer(args.file, args.darkmode)
    app.main_window.mainloop()
    

if __name__ == '__main__':
    arg_parser = argparse.ArgumentParser(description='Display a todo.txt file as a kanban and allow to edit it')
    arg_parser.add_argument('--file', help='Path to a todo.txt file', required=False, default='', type=str)
    arg_parser.add_argument('--darkmode', help='Is the UI should use dark theme', required=False, action='store_true')
    args = arg_parser.parse_args()
    main(args)
