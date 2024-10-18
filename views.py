import customtkinter as ctk
import tkinter as tk
import controlls as cmd
from tkinterdnd2 import DND_FILES
from model import model, save_model_and_tokenizer, load_model_and_tokenizer, predict, train_model
from functions_v2 import File
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from CTkListbox import *
import pandas as pd
from tkinter import filedialog

# Instances in an app class:
# analyze_File_data  -  an instance of a File class, created after choosing model from a list
# models_File_data   -  lis of instances of a File class


class MainWindow(ctk.CTkFrame):
    def __init__(self, root):
        super().__init__(root)
        self.root = root
        self.grid_rowconfigure(0, weight = 1)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=1)

        self.Drop_Box = DropBox(self)
        self.Drop_Box.grid(row=0, column=1, padx=10, pady=10, sticky='nsew')
        self.Left_Frame = Frame_Left_Ribbon(self)
        self.Left_Frame.grid(row=0, column=0, padx=(10,0), pady=10, sticky='ns')
        

class Frame_Left_Ribbon(ctk.CTkFrame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.grid_rowconfigure((0,2,3), weight=0)
        self.grid_rowconfigure(1, weight=1)

        self.ButtonNewModel = ctk.CTkButton(self,  text = 'Create new model', state='disabled', command=lambda: cmd.show_window(master.root, 'InfoNewModel'))
        self.ButtonNewModel.grid(row=0, padx=10, pady=(10,5), sticky='ew')
        self.ButtonTrainModel = ctk.CTkButton(self,  text = 'Add data', state='disabled', command=lambda:[self.create_window(master.root, 'TrainModelWindow') ,cmd.show_window(master.root, 'TrainModelWindow')])
        self.ButtonTrainModel.grid(row=2, padx=10, pady=5, sticky='ew')
        self.ButtonPlots = ctk.CTkButton(self,  text = 'Charts', state='disabled', command=lambda:[self.create_window(master.root, 'PlotsWindow') ,cmd.show_window(master.root, 'PlotsWindow')])
        self.ButtonPlots.grid(row=3, padx=10, pady=(5,10), sticky='ew')

        self.FrameSavedModels = Frame_Saved_Models(self, 'Saved models')
        self.FrameSavedModels.grid(row=1,padx=10, pady=5, sticky='nsew')

    def create_window(self, app, window_name):
        if window_name == 'PlotsWindow':
            window = PlotsWindow(app)
        elif window_name == 'TrainModelWindow':
            window = TrainModelWindow(app)
        app.windows[window_name] = window
        window.grid(row=0, column=0, sticky="nsew")


class Frame_Saved_Models(ctk.CTkFrame):
    def  __init__(self,master,frame_name):
        super().__init__(master)
        self.frame_name = frame_name
        self.Master = master
        self.model_picked = False
        self.saved_models_refresh()

    def saved_models_refresh(self):
        rows, models_names= self.search_models()
        self.grid_rowconfigure(len(rows), weight=0)
        self.grid_columnconfigure(0, weight=1)
        self.title = ctk.CTkLabel(self, text=self.frame_name, fg_color=['gray60','gray30'], text_color='white' , corner_radius=6)
        self.title.grid(row=0, padx=5, pady=(10, 0), sticky="ew")
        self.model_label = ctk.IntVar(value=-1)

        model_File_data = []
        self.model_names = []
        for i in range(len(rows)):
            model_name = str(models_names[i]).replace('.keras','')
            self.ButtonModel = ctk.CTkRadioButton(self,  text = model_name, value=i, variable=self.model_label, command=lambda: self.chose_model_data())
            self.ButtonModel.grid(row=i+1,padx=10, pady=(10,0), sticky = 'w')

            model_data = File(name=model_name)
            model_File_data.append(model_data)
            self.model_names.append(model_name)
        # Variable in an instance of an app -- models_File_data
        self.Master.master.root.models_File_data = model_File_data

    def search_models(self):
        models = cmd.look_for_models()
        rows = [i for i in range(len(models))]
        if len(rows) == 0:
            rows = []
        return rows, models
    
    def chose_model_data(self):
        # Creates instance of a File class, witch will be analized
        self.Master.master.root.analyze_File_data = self.Master.master.root.models_File_data[self.model_label.get()]
        # saves name in app
        self.Master.master.root.model_name = self.model_names[self.model_label.get()]

        # Enables a plot button
        self.Master.ButtonPlots.configure(state='normal')
        # Enables TrainModel Buttton
        self.model_picked = True
        if self.Master.master.Drop_Box.file_dropped:
            self.Master.ButtonTrainModel.configure(state="normal")


class DropBox(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        self.path_var = tk.StringVar()
        self.file_dropped = False
        self._path = ''

        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure((0,2), weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure((0,2), weight=0) 

        self.dropLabel = ctk.CTkLabel(self, text="Drop file here", font=("Helvetica", 16, "bold"))
        self.dropLabel.grid(row=0, column=0, columnspan=3, padx=5, pady=(5,0), sticky="nsew")

        self.entryWidget = ctk.CTkEntry(self)
        self.entryWidget.grid(row=1, column=0, columnspan=3, padx=5, pady=(5, 0), sticky="nsew")
        self.entryWidget.configure(state='readonly')
        self.entryWidget.drop_target_register(DND_FILES)
        self.entryWidget.dnd_bind("<<Drop>>", self.get_path)

        self.pathLabel = ctk.CTkLabel(self, text="File name", wraplength=400)
        self.pathLabel.grid(row=2, column=0, columnspan=3, padx=5, pady=(0, 5), sticky="sew")

        self.pathButton = ctk.CTkButton(self, text="Search file", command = self.get_path_2)
        self.pathButton.grid(row=2, column=0, padx=5, pady=(5, 5))


    def get_path(self, event):
        self.path_var.set(event.data)
        path = str(event.data).replace('{','').replace('}','')
        self.check_path(path)

    def get_path_2(self):
        path = filedialog.askopenfilename()
        self.check_path(path)

    def check_path(self, path):
        self.pathLabel.configure(text=path)
        if path.endswith('.pdf'):
            self._path = path
            self.dropLabel.configure(text = 'File succesfuly dropped', text_color=ctk.ThemeManager.theme["CTkButton"]["fg_color"])
            self.master.Left_Frame.ButtonNewModel.configure(state="normal")
            self.file_dropped = True
            self.master.root._pdfPath = path
            if self.master.Left_Frame.FrameSavedModels.model_picked:
                self.master.Left_Frame.ButtonTrainModel.configure(state="normal")
        else:
            self.dropLabel.configure(text = 'Wrong type of file ".pdf" expected', text_color = 'red')


class InfoNewModel(ctk.CTkFrame):
    def __init__(self, root):
        super().__init__(root)
        self.root = root
        self.grid_rowconfigure((0,1,2,3,5), weight = 0)
        self.grid_rowconfigure(4, weight = 1)
        self.grid_columnconfigure((0,1,2), weight = 1)
        numbers = [str(number) for number in range(1,12)]

        self.Label1 = ctk.CTkLabel(self, text = 'Name your AI model', font=("Helvetica", 16, "bold"), justify="center")
        self.Label1.grid(row=0, column=0, columnspan=3, padx=10, pady=10)
        self.EntryName = ctk.CTkEntry(self, placeholder_text=f"Name your model")
        self.EntryName.grid(row=1, column=0, columnspan=3, padx=10, pady=10)
        self.Label2 = ctk.CTkLabel(self, text = 'How many categories do you want to create?', font=("Helvetica", 16, "bold"), justify="center")
        self.Label2.grid(row=2, column=0, columnspan=3, padx=10, pady=10)
        self.ComboBox = ctk.CTkComboBox(self, values=numbers, command=self.get_number)
        self.ComboBox.grid(row=3, column=0, columnspan=3, padx=10, pady=(0, 10))
        self.ButtonNext = ctk.CTkButton(self,  text = 'Create new model', command=lambda:[self.prepare_file_data() ,self.create_window(root, 'NewModelWindow') ,cmd.show_window(root, 'NewModelWindow')]) 
        self.ButtonNext.grid(row=5, column=2, padx=10, pady=10, sticky = 'es')

    def prepare_file_data(self):
        self.root._model_name = self.EntryName.get()
        entered_texts = [var.get() for var in self._entries_var]
        self.root.data_from_file = File(self.root._pdfPath)
        self.root.data_from_file.categories = entered_texts

    def get_number(self, choise):
        self.ModelCategories = ctk.CTkFrame(self)
        self.ModelCategories.grid(row=4, column=0, columnspan=3, padx=10, pady=(0,10), sticky = 'ns')
        rows = [row for row in range(int(choise))]
        self.ModelCategories.grid_rowconfigure(rows, weight = 1)
        self._entries_var = []

        for i in range(int(choise)):
            entry = ctk.CTkEntry(self.ModelCategories, placeholder_text=f"Name your {i+1} category")
            entry.grid(row=i, padx=10, pady=10)
            self._entries_var.append(entry)

    def create_window(slef, app, window_name):
        window = NewModelWindow(app)
        app.windows[window_name] = window
        window.grid(row=0, column=0, sticky="nsew")


class NewModelWindow(ctk.CTkFrame):
    def __init__(self, root):
        super().__init__(root)
        self.root = root
        self.grid_rowconfigure((0,2), weight = 0)
        self.grid_rowconfigure(1, weight = 1)
        self.grid_columnconfigure((0,1,2), weight = 1)

        self.Label = ctk.CTkLabel(self, text = 'Categorize every transaction', font=("Helvetica", 16, "bold"), justify="center")
        self.Label.grid(row=0, column=0, columnspan=4, padx=10, pady=10)
        self.ScrollFrame = ScrollabableFrame(self, root.data_from_file)
        self.ScrollFrame.grid(row=1, column=0, columnspan=4, padx=10, pady=(0,10), sticky = 'nsew')
        self.ButtonPrevious = ctk.CTkButton(self, text = 'Confirm categories', command = lambda: [self.get_chossen_categories()])
        self.ButtonPrevious.grid(row=2, column=3, padx=10, pady=10)
         
    # After user categorize transactions, this function gets all categories and puts them into File class, makes list of labels, makes an AI model and saves it with tokenizer
    def get_chossen_categories(self):
        transaction_labels = []
        flag = -1
        for i in range(len(self.root.data_from_file.expences)):
            label = self.ScrollFrame.radio_button_vars[i].get()
            if label == -1:
                flag = 0
                self.InfoLabel = ctk.CTkLabel(self, text = 'Not every transaction categorized!',font=("Helvetica", 16, "bold"), text_color='red', justify="center")
                self.InfoLabel.grid(row=2, column=1)
                break
            else:
                transaction_labels.append(label)

        if flag == -1:
            self.root.data_from_file.add_exp_labels(transaction_labels)

            #Creates and trains model
            self.root.model1, self.root.tokenizer = model(self.root.data_from_file.exp_seq, transaction_labels)
            #Saves model and tokenizer
            save_model_and_tokenizer(self.root.model1, self.root.tokenizer, self.root._model_name, self.root._model_name+'_token')
            #Saves data from FileClass
            self.root.data_from_file.save_data(self.root._model_name)

            cmd.show_window(self.root, 'MainWindow')
            self.root.windows['MainWindow'].Left_Frame.FrameSavedModels.saved_models_refresh()


class ScrollabableFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, data: File, indexes: list[int] = [-1], predictions = [-1]):
        super().__init__(master)
        if indexes[0] == -1:
            rows = [row for row in range(2*len(data.expences))]
        else:
            rows = [row for row in range(2*len(indexes))]
        columns = [column for column in range(len(data.categories))]
        self.grid_rowconfigure(rows, weight = 0)
        self.grid_columnconfigure(columns, weight = 1)

        k=0
        self.radio_button_vars = []
        if indexes[0] == -1:
            for i in range(len(data.expences)):
                k += 2
                desc = data.expences.at[i,'description'] + ',   Kwota: ' + f"{data.expences.at[i,'amount']:.2f}" + ',   Data:  ' + str(data.expences.at[i,'date'])
                self.Label = ctk.CTkLabel(self, text = desc, justify="center")
                self.Label.grid(row=k, column = 0, columnspan=len(columns), padx=10, pady=10)

                xx = [2,0,5,5,2,5,2,1,2,6,5,5,6,1,2,2,0,2,5,5,5,5,5,1,1,5,5,2,1,3,2,5,5,1,2,5,2,0,5,5,5,2,2,5,2,1,3,2,5,5,5,6,2,5,2,5,1,5,1,1,5,6,1,2,2,5,5,1,0,2,1,5,5,5,2,5,2,5,6,5,4,5,1,1,5,5,1,2,1,5,2,5]
                
                button_var = ctk.IntVar(value=xx[i])
                # button_var = ctk.IntVar(value=-1)
                for j in range(len(columns)):
                    self.ButtonModel = ctk.CTkRadioButton(self,  text = data.categories[j], value=j, variable=button_var)
                    self.ButtonModel.grid(row=k+1,column=j, columnspan=1, padx=10, pady=(0,15))
                self.radio_button_vars.append(button_var)
        else:
            for i in range(len(indexes)):
                k += 2
                desc = data.expences.at[indexes[i],'description'] + ',   Kwota: ' + f"{data.expences.at[indexes[i],'amount']:.2f}" + ',   Data:  ' + str(data.expences.at[indexes[i],'date'])
                self.Label = ctk.CTkLabel(self, text = desc, justify="center")
                self.Label.grid(row=k, column = 0, columnspan=len(columns), padx=10, pady=10)
                
                button_var = ctk.IntVar(value=predictions[indexes[i]])
                for j in range(len(columns)):
                    self.ButtonModel = ctk.CTkRadioButton(self,  text = data.categories[j], value=j, variable=button_var)
                    self.ButtonModel.grid(row=k+1,column=j, columnspan=1, padx=10, pady=(0,15))
                self.radio_button_vars.append(button_var)



class PlotsWindow(ctk.CTkFrame):
    def __init__(self, root):
        super().__init__(root)
        self.root = root
        self.grid_columnconfigure(0, weight = 1)
        self.grid_rowconfigure(0, weight = 1)

        self.tab_viev = ctk.CTkTabview(self)
        self.tab_viev.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')

        self.tab_viev.add('Last Month')
        self.tab_viev.add('All Data')
        self.tab_viev.add('Rev/Exp')

        self.tab_viev.tab('Last Month').grid_columnconfigure(0, weight=1)
        self.tab_viev.tab('Last Month').grid_rowconfigure(0, weight=1)
        self.tab_viev.tab('All Data').grid_columnconfigure(0, weight=1)
        self.tab_viev.tab('All Data').grid_rowconfigure(0, weight=1)
        self.tab_viev.tab('Rev/Exp').grid_columnconfigure(0, weight=1)
        self.tab_viev.tab('Rev/Exp').grid_rowconfigure(0, weight=1)

        self.tab_viev.set('Last Month')
        self.last_month_plot = PlotsWindow_1(self.tab_viev.tab('Last Month'), self.root)
        self.last_month_plot.grid(row=0, column=0, sticky="nsew")
        self.all_data_plot = PlotsWindow_2(self.tab_viev.tab('All Data'), self.root)
        self.all_data_plot.grid(row=0, column=0, sticky="nsew")



class PlotsWindow_1(tk.PanedWindow):
    def __init__(self, root, master):
        super().__init__(root)
        self.master = master
        self.revenue = self.master.analyze_File_data.revenue
        self.expences = self.master.analyze_File_data.expences
        self.configure(orient=tk.VERTICAL)
        self.grid(row=0, column=0, sticky='nsew')
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Add to paned window frame for displaying plot
        self.plot_frame = ctk.CTkFrame(self)
        self.add(self.plot_frame)
        self.plot_frame.grid_rowconfigure(0, weight=1)
        self.plot_frame.grid_columnconfigure(0, weight=1)

        # Add to panned window frame for: list of transactions and checkboxes for manipulating plot 
        self.list_frame = ctk.CTkFrame(self)
        self.add(self.list_frame)
        self.list_frame.grid_rowconfigure((0,2), weight=0)
        self.list_frame.grid_rowconfigure(1, weight=1)
        self.list_frame.grid_columnconfigure((0,1,3), weight=0)
        self.list_frame.grid_columnconfigure(2, weight=1)

        # Left side of frame window: list of transactions and bottons
        self.date_button = ctk.CTkButton(self.list_frame, text='Date', width=100, state='disabled', command=self.sort_dates)
        self.date_button.grid(row=0, column=0, padx=(5,0), pady=5)
        self.sum_button = ctk.CTkButton(self.list_frame, text='Sum', width=80, state='disabled',  command=self.sort_sums)
        self.sum_button.grid(row=0, column=1, padx=5, pady=5)
        self.desc_button = ctk.CTkButton(self.list_frame, text='Description', hover=False)
        self.desc_button.grid(row=0, column=2, pady=5, sticky='ew')
        self.record_list = ctk.CTkScrollableFrame(self.list_frame)
        self.record_list.grid(row=1, column=0, padx=(5,0), pady=(0,5), rowspan=2, columnspan=3, sticky='nsew')

        # Right side of frame window: Create chekbox butttons for manipulating plots in scrollbar
        self.scroll_bar = ctk.CTkScrollableFrame(self.list_frame)
        self.scroll_bar.grid(row=1, column=3, padx=5, pady=(0,5), sticky='ns')
        rows = len(self.master.analyze_File_data.categories_plus)
        self.scroll_bar.grid_rowconfigure(rows, weight = 0)
        self.scroll_bar.grid_columnconfigure(0, weight = 0)
        self.dropdown_list = ctk.CTkComboBox(self.list_frame, values=self.master.analyze_File_data.periods_str, state='readonly', command=self.select_period)
        self.dropdown_list.grid(row=0, column=3, padx=5, sticky='ew')
        self.dropdown_list.set(self.master.analyze_File_data.periods_str[-1])
        self.period = self.master.analyze_File_data.periods[-1]

        self.checkbox_vars = []
        i=0 
        for category in self.master.analyze_File_data.categories_plus:
            checkbox_var = ctk.IntVar(value=1)
            self.checkbox_button = ctk.CTkCheckBox(self.scroll_bar, text=category, variable=checkbox_var, onvalue=1, offvalue=0, command=lambda: self.get_plot(self.period))
            self.checkbox_button.grid(row=i, column=1, padx=5, pady=5)
            self.checkbox_vars.append(checkbox_var)
            i += 1

        # Add Home Button
        self.button = ctk.CTkButton(self.list_frame, text = 'Home Page', command=lambda: cmd.show_window(self.master, 'MainWindow'))
        self.button.grid(row=2,column=3, padx=5, pady=(0,5), sticky='ew')

        self.cnt1, self.cnt2, self.cnt3, self.cnt4 = 0, 0, 0, 0

        # Show plot
        self.get_plot()    


    def on_click(self, event):
        # Clear list
        self.record_list.destroy()
        list_categories = [self.master.analyze_File_data.categories_plus[i] for i in range(len(self.checkbox_vars)) if self.checkbox_vars[i].get() == 1]
        category = list_categories[event.index]

        self.event = event
        self.date_button.configure(state='normal')
        self.sum_button.configure(state='normal')

        self.record_list = ctk.CTkScrollableFrame(self.list_frame)
        self.record_list.grid(row=1, column=0, padx=(5,0), pady=(0,5), rowspan=2, columnspan=3, sticky='nsew')
        self.record_list.grid_columnconfigure((0,1), weight=0)
        self.record_list.grid_columnconfigure(2, weight=1)
        self.record_list.grid_rowconfigure(0, weight=0)

        if category == 'Przychody':
            data_extract = self.revenue 
            data_extract['Kategoria'] = category
        else:
            data_extract = self.expences

        month_start, month_end = cmd.last_month(self.period)
        j = 0
        for i in range(len(data_extract)):
            if month_start <= data_extract['date'].iloc[i] <= month_end: 
                if data_extract.loc[i,'Kategoria'] == category:
                    self.record_list.grid_rowconfigure(j, weight=1)
                    self.date_frame = ctk.CTkFrame(self.record_list)
                    self.date_frame.grid(row=j, column=0, pady=(0,9), sticky='ew')
                    self.sum_frame = ctk.CTkFrame(self.record_list)
                    self.sum_frame.grid(row=j, column=1, padx=5, pady=(0,9), sticky='ew')
                    self.desc_frame = ctk.CTkFrame(self.record_list)
                    self.desc_frame.grid_columnconfigure(0, weight=1)
                    self.desc_frame.grid_columnconfigure((1,2), weight=0)
                    self.desc_frame.grid(row=j, column=2, pady=(0,9), sticky='ew')
                    self.date_label = ctk.CTkLabel(self.date_frame, text=data_extract.loc[i,'date'], width=73)
                    self.date_label.grid(row=0, column=0, padx=10, sticky='ew')
                    self.sum_label = ctk.CTkLabel(self.sum_frame, text=str(data_extract.loc[i,'amount']), width=60)
                    self.sum_label.grid(row=0, column=0, padx=10, sticky='ew')
                    self.desc_label = ctk.CTkLabel(self.desc_frame, text=data_extract.loc[i,'description'])
                    self.desc_label.grid(row=0, column=0, padx=10, sticky='w')
                    if category != 'Przychody':
                        self.combobox_choise = category
                        self.change_button = ctk.CTkButton(self.desc_frame, text = 'Change', width=50, command=lambda i=i: self.change_category(i, self.expences, self.combobox_choise)) 
                        self.change_button.grid(row=0, column=1, sticky='e')
                        self.combobox = ctk.CTkComboBox(self.desc_frame, values=self.master.analyze_File_data.categories, state='readonly', command=self.pick_category)
                        self.combobox.set(category)
                        self.combobox.grid(row=0, column=2)
                    j = j + 1    

    def pick_category(self, choise):
        self.combobox_choise = choise

    def change_category(self, j, exp1, new_cat):
        for i in range(len(self.master.analyze_File_data.categories)):
            if new_cat == self.master.analyze_File_data.categories[i]:
                new_label = i
        exp1.loc[j,'Labels'] = new_label
        exp1.loc[j,'Kategoria'] = new_cat
        self.master.analyze_File_data.expences.loc[j,'Labels'] = new_label
        self.master.analyze_File_data.expences.loc[j,'Kategoria'] = new_cat
        exp1.sort_values(by='date', ascending=True, inplace=True, ignore_index=True)
        self.master.analyze_File_data.expences.sort_values(by='date', ascending=True, inplace=True, ignore_index=True)
        self.master.analyze_File_data.save_data(self.master.model_name)
        self.master.analyze_File_data = File(name=self.master.model_name)
        self.get_plot(self.period)
        self.on_click(self.event)

    def sort_dates(self):
        if self.cnt1 % 2 == 1:
            self.expences.sort_values(by='date', ascending=True, inplace=True, ignore_index=True)
            self.master.analyze_File_data.expences.sort_values(by='date', ascending=True, inplace=True, ignore_index=True)
        else:
            self.expences.sort_values(by='date', ascending=False, inplace=True, ignore_index=True)
            self.master.analyze_File_data.expences.sort_values(by='date', ascending=False, inplace=True, ignore_index=True)
        self.cnt1 += 1

        if self.cnt2 % 2 == 1:
            self.revenue.sort_values(by='date', ascending=True, inplace=True, ignore_index=True)
        else:
            self.revenue.sort_values(by='date', ascending=False, inplace=True, ignore_index=True)
        self.cnt2 += 1
        self.on_click(self.event)

    def sort_sums(self):
        if self.cnt3 % 2 == 1:
            self.expences.sort_values(by='amount', ascending=True, inplace=True, ignore_index=True)
            self.master.analyze_File_data.expences.sort_values(by='amount', ascending=True, inplace=True, ignore_index=True)
        else:
            self.expences.sort_values(by='amount', ascending=False, inplace=True, ignore_index=True)
            self.master.analyze_File_data.expences.sort_values(by='amount', ascending=False, inplace=True, ignore_index=True)
        self.cnt3 += 1

        if self.cnt4 % 2 == 1:
            self.revenue.sort_values(by='amount', ascending=True, inplace=True, ignore_index=True)
        else:
            self.revenue.sort_values(by='amount', ascending=False, inplace=True, ignore_index=True)
        self.cnt4 += 1
        self.on_click(self.event)

    def select_period(self, choise):
        for i in range(len(self.master.analyze_File_data.periods_str)):
            if choise == self.master.analyze_File_data.periods_str[i]:
                self.period = self.master.analyze_File_data.periods[i]
        self.get_plot(self.period)

    def get_plot(self, period = 'last'):
        if period == 'last':
            self.fig, self.bars, self.cursor = cmd.get_bar_plot(self.master.analyze_File_data, self.checkbox_vars)
        else:
            self.fig, self.bars, self.cursor = cmd.get_bar_plot(self.master.analyze_File_data, self.checkbox_vars, period)
        canvas = FigureCanvasTkAgg(self.fig, self.plot_frame)
        canvas.draw()
        canvas.get_tk_widget().grid(row=0, column=0, sticky='nsew')

        # Interactive bars 
        self.cursor.connect('add', self.on_click)
        

















class PlotsWindow_2(tk.PanedWindow):
    def __init__(self, root, master):
        super().__init__(root)
        self.master = master
        self.configure(orient=tk.VERTICAL)
        self.grid(row=0, column=0, sticky='nsew')
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self.plot_frame = ctk.CTkFrame(self)
        self.add(self.plot_frame)
        self.plot_frame.grid_rowconfigure(0, weight=1)
        self.plot_frame.grid_columnconfigure(0, weight=1)

        self.list_frame = ctk.CTkFrame(self)
        self.add(self.list_frame)
        self.list_frame.grid_rowconfigure(0, weight=1)
        self.list_frame.grid_rowconfigure(1, weight=0)
        self.list_frame.grid_columnconfigure(0, weight=1)
        self.list_frame.grid_columnconfigure(1, weight=0)
        
        self.listbox = CTkListbox(self.list_frame)
        self.listbox.grid(row=0, column=0, rowspan=3, sticky='nsew')
        self.button = ctk.CTkButton(self.list_frame, text = 'Home Page', command=lambda: cmd.show_window(self.master, 'MainWindow'))
        self.button.grid(row=1,column=1, padx=10, pady=10)

        # Create chekbox butttons for manipulating plots in scrollbar
        self.scroll_bar = ctk.CTkScrollableFrame(self.list_frame)
        self.scroll_bar.grid(row=0, column=1, padx=5, pady=5, sticky='ns')
        rows = len(self.master.analyze_File_data.categories_plus)
        self.scroll_bar.grid_rowconfigure(rows, weight = 1)
        self.scroll_bar.grid_columnconfigure(0, weight = 0)

        self.checkbox_vars = []
        i=0 
        for category in self.master.analyze_File_data.categories_plus:
            checkbox_var = ctk.IntVar(value=1)
            self.checkbox_button = ctk.CTkCheckBox(self.scroll_bar, text=category, variable=checkbox_var, onvalue=1, offvalue=0, command=self.get_plot)
            self.checkbox_button.grid(row=i, column=1, padx=10, pady=10)
            self.checkbox_vars.append(checkbox_var)
            i += 1

        self.get_plot()       


    def get_plot(self):
        self.fig, self.bars, self.cursor = cmd.get_combined_bar_plot(self.master.analyze_File_data, self.checkbox_vars)
        canvas = FigureCanvasTkAgg(self.fig, self.plot_frame)
        canvas.draw()
        canvas.get_tk_widget().grid(row=0, column=0, sticky='nsew')

        # Interactive bars 
        self.cursor.connect('add', self.on_click)

    def on_click(self, event):
        # Clear list firstly
        ...
        # self.listbox.delete(0, 'end')
        # list_categories = [self.master.analyze_File_data.categories_plus[i] for i in range(len(self.checkbox_vars)) if self.checkbox_vars[i].get() == 1]
        # category = list_categories[event.index]
        
        # j = 0
        # if category == 'Przychody':
        #     for i in range(len(self.master.analyze_File_data.revenue)):
        #             if self.master.analyze_File_data.revenue['Data transakcji'].iloc[i] >= cmd.last_month(self.master.analyze_File_data.revenue): 
        #                 row = str(self.master.analyze_File_data.revenue.loc[i,'Data transakcji']) + '     ,'
        #                 row = row + self.master.analyze_File_data.revenue.loc[i,'Kwota'] + '     ,'
        #                 row = row + self.master.analyze_File_data.revenue.loc[i,'Opis operacji']
        #                 self.listbox.insert(j, row)
        #                 j = j + 1
        # else:
        #     for i in range(len(self.master.analyze_File_data.expences)):
        #         if self.master.analyze_File_data.expences.loc[i,'Kategoria'] == category:
        #             if self.master.analyze_File_data.expences['Data transakcji'].iloc[i] >= cmd.last_month(self.master.analyze_File_data.revenue):
        #                 row = str(self.master.analyze_File_data.expences.loc[i,'Data transakcji']) + '     ,'
        #                 row = row + self.master.analyze_File_data.expences.loc[i,'Kwota'] + '     ,'
        #                 row = row + self.master.analyze_File_data.expences.loc[i,'Opis operacji']
        #                 self.listbox.insert(j, row)
        #                 j = j + 1
            

                



class TrainModelWindow(ctk.CTkFrame):
    def __init__(self, root):
        super().__init__(root)
        self.root = root
        self.grid_rowconfigure((0,2), weight = 0)
        self.grid_rowconfigure(1, weight = 1)
        self.grid_columnconfigure((0,1,2), weight = 1)

        self.old_data = root.analyze_File_data

        # Load given file
        self.new_data = File(root._pdfPath)
        self.new_data.categories = self.old_data.categories
        # Load AI model and tokenizer
        self.model, self.tokenizer = load_model_and_tokenizer(root.model_name, root.model_name+'_token')
        # Predict classes of transactions, catch those transactions that needs verification
        self.predicted_classes, self.indexes_to_correct = predict(self.model, self.tokenizer, self.new_data)

        # Display transactions that need verification
        self.Label = ctk.CTkLabel(self, text = 'Categorize transactions', font=("Helvetica", 16, "bold"), justify="center")
        self.Label.grid(row=0, column=0, columnspan=4, padx=10, pady=10)
        self.ScrollFrame = ScrollabableFrame(self, self.new_data, self.indexes_to_correct, self.predicted_classes)
        self.ScrollFrame.grid(row=1, column=0, columnspan=4, padx=10, pady=(0,10), sticky = 'nsew')
        self.ButtonPrevious = ctk.CTkButton(self, text = 'Confirm', command=lambda:[self.organize_File_data(), self.organize_AI_model(), cmd.show_window(root, 'MainWindow'), root.windows['MainWindow'].Left_Frame.FrameSavedModels.saved_models_refresh()])
        self.ButtonPrevious.grid(row=2, column=3, padx=10, pady=10)
        
    def organize_File_data(self):
        transaction_labels = []
        j=0
        for i in range(len(self.new_data.expences)):
            if i == self.indexes_to_correct[j]:
                transaction_labels.append(self.ScrollFrame.radio_button_vars[j].get())
                if j<len(self.indexes_to_correct)-1:
                    j+=1
            else:
                transaction_labels.append(self.predicted_classes[i])  
        # Add new data to old data
        self.old_data.add_new_data(self.new_data)
        self.old_data.add_exp_labels(transaction_labels)
        # Save refreshed old data
        self.old_data.save_data(self.root.model_name)

    def organize_AI_model(self):
        #Creates and trains model
        self.model, self.tokenizer = model(self.old_data.exp_seq, self.old_data.expences['Labels'])
        #Saves model and tokenizer
        save_model_and_tokenizer(self.model, self.tokenizer, self.root.model_name, self.root.model_name+'_token')

        # train_model(self.model, self.tokenizer, self.old_data)
        # save_model_and_tokenizer(self.model, self.tokenizer, self.root.model_name, self.root.model_name+'_token')




