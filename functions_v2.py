import tabula
import pandas as pd
import pickle
import numpy as np
import datetime
import re


class File:
    def __init__(self, path='', name='') -> 'File':
        if name == '':
            self._initializing = True
            self.path = path
            self.table = self.get_dataframe(self.path)
            self.revenue, self.expences = self.separate(self.table)
            self._initializing = False
            self.exp_seq = self.expences
        else:
            self._initializing = True
            self.load_data(name)
            self.exp_seq = self.expences
            self.summarize()
            self._initializing = False

    def __str__(self):
        # Do zmiany - musi zwracać string
        return(self.table)


    @property
    def path(self) -> str:
        return self._path

    @path.setter
    def path(self, path: str) -> None:
        if not self._initializing:
            raise ValueError('Operation reserved only for initializing')
        elif not str(path).strip().endswith('.pdf'):
            raise ValueError('Invalid file')
        self._path = path
       

    @property
    def table(self) -> pd.DataFrame:
        return self._table
    
    @table.setter
    def table(self, table: pd.DataFrame) -> None:
        if not (self._initializing or self._concatinating):
            raise ValueError('Operation reserved only for initializing and concatinating')
        self._table = table
        

    @property
    def revenue(self) -> pd.DataFrame:
        return self._revenue
    
    @revenue.setter
    def revenue(self, rev: pd.DataFrame) -> None:
        if not (self._initializing or self._concatinating):
            raise ValueError('Operation reserved only for initializing and concatinating')
        self._revenue = rev


    @property
    def expences(self) -> pd.DataFrame:
        return self._expences
    
    @expences.setter
    def expences(self, exp: pd.DataFrame) -> None:
        if not (self._initializing or self._concatinating):
            raise ValueError('Operation reserved only for initializing and concatinating')
        self._expences = exp


    @property
    def exp_seq(self) -> list[str]:
        return self._exp_seq
    
    @exp_seq.setter
    def exp_seq(self, exp: pd.DataFrame) -> None:
        self._exp_seq = [exp.at[i,'description'] for i in range(len(exp))]


    @property
    def categories(self) -> list[str]:
        return self._categories
    
    @categories.setter
    def categories(self, cat: list) -> None:
        self._categories = cat
        self._categories_plus = self._categories.copy()
        self._categories_plus.append('Przychody')


    #categories with addition of 'revenue' 
    @property
    def categories_plus(self) -> list[str]:
        return self._categories_plus

    
    @property
    def model_name(self) -> str:
        return self._model_name
    
    @model_name.setter
    def model_name(self, name) -> None:
        self._model_name = name

    @property
    def summary(self) -> pd.DataFrame:
        return self._summary
    
    @property
    def periods(self) -> list:
        return self._periods
    
    @property
    def periods_str(self) -> list:
        return self._periods_str

    def get_dataframe(self, file: str) -> pd.DataFrame:
        tables = tabula.read_pdf(file, pages='all', lattice=True)
        valid_columns = {}
        date_pattern = r'\d+-\d+-\d+'
        amount_pattern = r'-{1}[0-9\s]+,{1}\d{2}'
        desc_pattern = r'[A-Z]+\w+[A-Z]'

        for i, table in enumerate(tables):
            if i == 1:
                rows = []
                data = table
                data = data.dropna(how='all').reset_index(drop=True)
                data.columns = range(len(data.columns))
                
                for col_name in data.columns:
                    for i in range(6):
                        v = data.at[i, col_name]
                        v = v.replace('\r',' ')
                        
                        if re.match(amount_pattern, v):
                            valid_columns[col_name] = 'amount'
                            rows.append(i)
                            break
                        elif re.match(date_pattern, v):
                            if 'date' not in valid_columns.values():
                                valid_columns[col_name] = 'date'
                            rows.append(i)
                            break
                        elif re.match(desc_pattern, v):
                            valid_columns[col_name] = 'description'
                            break
                
                # delete first rows if they dose not match the rest
                if 0 not in rows:
                    for i in range(min(rows)):
                        data = data.drop(index=i).reset_index(drop=True)

                # delete unnecesery columns, rename rest
                data = self.prepare_columns(data, valid_columns)

            elif i != 0:
                data_2 = table
                data_2.columns = range(len(data_2.columns))
                data_2 = self.prepare_columns(data_2, valid_columns)
                data = pd.concat([data, data_2], ignore_index=True)

        data_cleaned = data.dropna(how='all').reset_index(drop=True)
        if data_cleaned.iloc[-1].isnull().any():
            data_cleaned = data_cleaned.drop(index=data_cleaned.index[-1])


        # prepare data
        for i, row in data_cleaned.iterrows():
            description = row['description']
            amount = row['amount']

            if match := re.search(date_pattern, description):
                data_cleaned.at[i, 'date'] = match.group()
                data_cleaned.at[i, 'description'] = description[:-28]

            if (x := description.find('/')) != -1:
                data_cleaned.at[i, 'description'] = description[0:x]

            if data_cleaned.at[i, 'description'].startswith('ZAKUP'):
                data_cleaned.at[i, 'description'] = data_cleaned.at[i, 'description'][23:]

            if (x := description.find('ZAKUP PRZY')) > 0:
                data_cleaned.at[i, 'description'] = description[0:x]

            if description.endswith('INTERNET'):
                     data_cleaned.at[i, 'description'] = description[:-35]

            if match := re.search(r'PRZELEW NA TWOJE CELE', description):
                data_cleaned.at[i, 'description'] = match.group()

            if match := re.search(r'[\sA-Za-z]+', amount):
                data_cleaned.at[i, 'amount'] = re.sub(r'[\sA-Za-z]+', '', amount)

            data_cleaned.at[i, 'date'] = self.convert_to_date_type(data_cleaned.at[i, 'date'])

        data_cleaned['description'] = data_cleaned['description'].str.replace('\r',' ')
        data_cleaned['amount'] = data_cleaned['amount'].str.replace(',','.').replace(' ','').astype(float) 

        return data_cleaned

    # def get_dataframe(self, file: str) -> pd.DataFrame:
    #     tables = tabula.read_pdf(file, pages='all', lattice=True)
    #     for i in range(len(tables)):
    #         if i == 1:
    #             data = tables[i]
    #             data.columns = ['Data ksiegowania','Data operacji','Opis operacji','Kwota','Saldo po operacji']
    #             data = data.drop(index=1)
    #         elif i != 0:
    #             data_2 = tables[i]
    #             data_2.columns = ['Data ksiegowania','Data operacji','Opis operacji','Kwota','Saldo po operacji']
    #             data = pd.concat([data, data_2], ignore_index=True)
    #     data_cleaned = data.dropna(how='all')
    #     data_cleaned = data_cleaned.reset_index(drop=True)
    #     data_cleaned = data_cleaned.drop(index=data_cleaned.index[-1])

    #     # Extracts real transaction dates from descriptions| delete dates from describtions| adds new column to table 
    #     real_dates = []
    #     for i in range(len(data_cleaned)):
    #         if data_cleaned.loc[i,'Opis operacji'].startswith('ZAKUP PRZY UŻYCIU KARTY'):
    #             date = self.convert_to_date_type(data_cleaned.loc[i,'Opis operacji'][-10:])
    #             real_dates.append(date)
    #             data_cleaned.loc[i, 'Opis operacji'] = data_cleaned.loc[i, 'Opis operacji'][23:-28]
    #         elif data_cleaned.loc[i,'Opis operacji'].startswith('PRZELEW NA TWOJE CELE'):
    #             data_cleaned.loc[i, 'Opis operacji'] = data_cleaned.loc[i, 'Opis operacji'][:21]
    #             date = self.convert_to_date_type(data_cleaned.loc[i,'Data operacji'])
    #             real_dates.append(date)
    #         else:
    #             date = self.convert_to_date_type(data_cleaned.loc[i,'Data operacji'])
    #             real_dates.append(date)
    #     data_cleaned['Data transakcji'] = real_dates
    #     return data_cleaned   
        

    def separate(self, table: pd.DataFrame) -> list[pd.DataFrame]:
        headers = table.columns.to_list()
        rev = pd.DataFrame(columns=headers)
        exp = pd.DataFrame(columns=headers)
        rev_i, exp_i = 0, 0

        for i in range(len(table)):
            if table.at[i,'amount'] > 0:
                rev.loc[rev_i] = table.loc[i]
                rev_i += 1
            else:
                exp.loc[exp_i] = table.loc[i]
                exp_i += 1

        exp = exp.assign(Labels=None)
        exp = exp.assign(Kategoria=None)
        return [rev, exp]
    

    def add_exp_labels(self, labels: list) -> None:
        str_labels = [self.categories[label] for label in labels]
        st = min(self.expences[self.expences['Labels'].isna()].index)
        self.expences.loc[st:, 'Labels'] = labels
        self.expences.loc[st:, 'Kategoria'] = str_labels

    def save_data(self, path) -> None:
        packed_data = {
            'table': self.table,
            'revenue': self.revenue,
            'expences': self.expences,
            'categories': self.categories, 
            'path': self.path
        }
        with open(path + '_File_Class_Data.pickle', 'wb') as f:
            pickle.dump(packed_data, f)

    def load_data(self, path) -> None:
        with open(path + '_File_Class_Data.pickle', 'rb') as f:
            data_loaded = pickle.load(f)
            self.path = data_loaded['path']
            self.table = data_loaded['table']
            self.revenue = data_loaded['revenue']
            self.expences = data_loaded['expences']
            self.categories = data_loaded['categories']

    def summarize(self) -> None:
        periods = []
        for i in range(len(self.table)):
            date = self.table.at[i,'date']
            if [date.month, date.year] not in periods:
                periods.append([date.month, date.year])

        column_names = ['Okres', 'Kategoria', 'Suma']
        for i in range(len(periods)):
            dt = pd.DataFrame(columns=column_names)
            dt['Kategoria'] = self.categories_plus
            [M, Y] = periods[i]
            sums = []
            for cat in self.categories_plus:
                k_exp, acc = 0, 0
                for j in range(len(self.table)):
                    date = self.table.at[j,'date']
                    amount = self.table.at[j, 'amount']
                    if date.month == M and date.year == Y:
                        if amount < 0:
                            if cat != 'Przychody' and cat == self.expences['Kategoria'].iloc[k_exp]:
                                acc = acc + abs(self.expences['amount'].iloc[k_exp])
                            k_exp += 1
                        else:
                            if cat == 'Przychody':
                                acc = acc + abs(amount) 
                    else:
                        if amount < 0:
                            k_exp += 1 

                sums.append(acc)  
            dt['Suma'] = sums
            dt['Okres'] = [periods[i] for _ in range(len(self.categories_plus))]
            if i == 0:
                summary = dt
            else:    
                summary = pd.concat([summary, dt], ignore_index=True)

        self._periods = []
        for i in range(len(summary)):
            if summary.loc[i,'Okres'] not in self.periods:
                self._periods.append(summary.loc[i,'Okres'])
        self._periods_str = [str(period[0]) + '-' + str(period[1]) for period in self._periods]

        self._summary = summary



    def add_new_data(self, new_data: 'File') -> None:
        self._concatinating = True
        self.table = pd.concat([self.table, new_data.table], ignore_index=True)
        self.expences = pd.concat([self.expences, new_data.expences], ignore_index=True)
        self.revenue = pd.concat([self.revenue, new_data.revenue], ignore_index=True)
        self.exp_seq = self.expences
        self.summarize()
        self._concatinating = False

    def convert_to_date_type(self, date: str) -> datetime.date:
        Y, M, D = date.split('-')
        date_dt = datetime.date(int(Y), int(M), int(D))
        return date_dt

    def prepare_columns(self, data: pd.DataFrame, valid_columns: dict) -> pd.DataFrame:
        for col_name in data.columns:
            if col_name not in valid_columns:
                del data[col_name]
        data.columns = valid_columns.values()
        return data
