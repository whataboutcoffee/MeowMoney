import asyncpg
import datetime
from typing import Any, List, Tuple, Coroutine
from aiogram.types import Message
from functools import wraps


class Counter:
    def __init__(self) -> None:
        self.count = 0
        
    def __call__(self, *args: Any, **kwds: Any) -> Any:
        self.count += 1
        return self.count
    

class DataBase:
    def __init__(
            self,
            server: str,
            database: str,
            port: str,
            username: str,
            password: str
            ) -> None:
        self.server = server
        self.database = database
        self.port = port
        self.username = username
        self.password = password
    
    # @staticmethod
    # async def proc_db_error(func: Coroutine,
    #                         msg: Message,
    #                         *args,
    #                         **kwargs):
    #     try:
    #         return await func(*args, **kwargs)
    #     except:
    #         await msg.answer("Что-то пошло не так - про блемы с базой данных. Попробуйте позднее")
    
    async def create_pool(self) -> asyncpg.Pool:
        return await asyncpg.create_pool(
            user=self.username,
            password=self.password,
            host=self.server,
            port=self.port,
            database=self.database
        )
    
    def raise_db_error(func: Coroutine):
        """Decorator raising an error with the database error text if any exception raised"""
        @wraps(func)
        async def inner(*args, **kwargs):
            try:
                res = await func(*args, **kwargs)
                return res
            except Exception as ex:
                raise ValueError("Что-то пошло не так - проблемы с базой данных. Попробуйте позднее") from ex
        return inner
    
    @staticmethod
    @raise_db_error
    async def check_categories(
            conn: asyncpg.Connection,
            user_id: int,
            inp_ctgrs: set,
            type: str
            ):
        db_ctgrs = await conn.fetch("SELECT category FROM categories WHERE user_id = ($1) AND type = ($2)", user_id, type)
        ctgrs = {record[0] for record in db_ctgrs}
        new_ctgrs = inp_ctgrs.difference(ctgrs)
        if new_ctgrs != set():
            return new_ctgrs
        return None
    
    @staticmethod
    @raise_db_error
    async def return_all_ctgrs(
            conn: asyncpg.Connection,
            user_id: int
    ) -> list:
        """Returns the list of the categories associated with specified user id"""
        res = await conn.fetch("SELECT category FROM categories WHERE user_id = ($1)", user_id)
        return set([r[0] for r in res])


    @staticmethod
    @raise_db_error
    async def add_operation_db(
            conn: asyncpg.Connection,
            user_id: int,
            date: datetime.datetime.date,
            type_oper: str,
            ctgrs: List[str],
            vals: List[float]
            ) -> None:
        args = [(user_id, date, type_oper, ctgrs[i], vals[i]) for i in range(len(ctgrs))]
        await conn.executemany("INSERT INTO history (user_id, date, type, category, value) VALUES ($1, $2, $3, $4, $5)", args)                       
    

    @staticmethod
    @raise_db_error
    async def add_categories(
        conn: asyncpg.Connection,
        user_id: int,
        ctgrs: set,
        type_oper: str
    ) -> None:
        args = [(user_id, c, type_oper) for c in ctgrs]
        await conn.executemany("INSERT INTO categories (user_id, category, type) VALUES ($1, $2, $3)", args)

    # @staticmethod
    # @raise_db_error
    # async def fetch_old(
    #     conn: asyncpg.Connection,
    #     user_id: int,
    #     date1: datetime.datetime.date,
    #     date2: datetime.datetime.date,
    #     ctgrs_lst: List[List[str]]
    # ) -> List[list]:
        
    #     records: list = []
    #     ctgrs_not_found = set()
    #     async with conn.transaction():
    #         for row in ctgrs_lst:
    #             ctgr = row[0]
    #             val = row[2]
    #             if row[3] == '+-':
    #                 delta = row[4]
    #                 bot_lim = val - delta
    #                 top_lim = val + delta
    #                 r = await conn.fetch("SELECT category, value, oper_id, date, type FROM history WHERE category = ($1) AND value > ($2) AND value < ($3) AND date >= ($4) AND date <= ($5) AND user_id = ($6)", ctgr, bot_lim, top_lim, date1, date2, user_id)
    #             elif row[1] == row[2] == row[3] == row[4] == None:
    #                 r = await conn.fetch("SELECT category, value, oper_id, date, type FROM history WHERE category = ($1) AND date >= ($2) AND date <= ($3) AND user_id = ($4)", ctgr, date1, date2, user_id)
    #             else:
    #                 if row[1] == '=':
    #                     operator = '='
    #                 elif row[1] == '>':
    #                     operator = '>'
    #                 elif row[1] == '<':
    #                     operator = '<' # prevention of sql injections, to transmit for a query only "=", "<" or ">", not anything user wants to transmit
    #                 else:
    #                     raise ValueError('Некорректный оператор сравнения, допустимо только "=", "<" или ">"')
    #                 r = await conn.fetch(f"SELECT category, value, oper_id, date, type FROM history WHERE category = ($1) AND value {operator} ($2) AND date >= ($3) AND date <= ($4) AND user_id = ($5)", ctgr, val, date1, date2, user_id)
    #             if r != []:
    #                 records += r
    #             else:
    #                 ctgrs_not_found.add(ctgr)
    #             records.sort(key = lambda x: x[3])
                
    #     return [(r[0], r[1], r[3], r[4]) for r in records], [(r[2],) for r in records], ctgrs_not_found
    
    
    @staticmethod
    @raise_db_error
    async def fetch(
        conn: asyncpg.Connection,
        user_id: int,
        date1: datetime.datetime.date,
        date2: datetime.datetime.date,
        ctgrs_lst: List[List[str]],
        user_ctgrs: set,
        group_by: bool = False
    ) -> List[list]:
        c = Counter()
        query_lst = []
        args = []
        ctgrs = set()
        for row in ctgrs_lst:
            ctgr = row[0]
            val = row[2]
            if row[3] == '+-':
                delta = row[4]
                bot_lim = val - delta
                top_lim = val + delta
                temp_query = f'category = (${c()}) AND value > (${c()}) AND value < (${c()}) AND date >= (${c()}) AND date <= (${c()}) AND user_id = (${c()})'
                temp_args = [ctgr, bot_lim, top_lim, date1, date2, user_id]
            elif row[1] == row[2] == row[3] == row[4] == None:
                temp_query = f'category = (${c()}) AND date >= (${c()}) AND date <= (${c()}) AND user_id = (${c()})'
                temp_args = [ctgr, date1, date2, user_id]
            else:
                if row[1] == '=':
                    operator = '='
                elif row[1] == '>':
                    operator = '>'
                elif row[1] == '<':
                    operator = '<' # prevention of sql injections, to transmit for a query only "=", "<" or ">", not anything user wants to transmit
                else:
                    raise ValueError('Некорректный оператор сравнения, допустимо только "=", "<" или ">"')
                temp_query = f'category = (${c()}) AND value {operator} (${c()}) AND date >= (${c()}) AND date <= (${c()}) AND user_id = (${c()})'
                temp_args = [ctgr, val, date1, date2, user_id]
            query_lst.append(temp_query)
            args += temp_args
            ctgrs.add(ctgr)
        query_str = ' OR '.join(query_lst)
        if group_by:
            query = 'SELECT category, SUM(value), type FROM history WHERE ' + query_str + ' GROUP BY category, type ORDER BY type DESC, SUM(value)'
        else:
            query = 'SELECT category, value, oper_id, date, type FROM history WHERE ' + query_str + ' ORDER BY date'
        records = await conn.fetch(query, *args)
        ctgrs_not_found = ctgrs.difference(user_ctgrs)
        
        if group_by:
            return [(r[0], r[1], None, r[2]) for r in records], [], ctgrs_not_found
        else:
            return [(r[0], r[1], r[3], r[4]) for r in records], [(r[2],) for r in records], ctgrs_not_found


    @staticmethod
    @raise_db_error
    async def del_from_db(
        conn: asyncpg.Connection,
        oper_ids: List[int]
    ) -> None:
        await conn.executemany("DELETE FROM history WHERE oper_id = ($1)", oper_ids)
    

    @staticmethod
    @raise_db_error
    async def fetch_with_ids(
        conn: asyncpg.Connection,
        oper_ids: List[int]
    ):
        res = await conn.fetch('SELECT category, value, oper_id, date, type FROM history WHERE oper_id = ANY ($1)', oper_ids)
        return res






