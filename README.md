# test_task
Проект реализует rest api доступ к базе данных.
Существует два варианта запуска
1) Запуск локально программы через main.py, для него необходимо установить на систему postgres и поменять данные в test_db_params на данные своей базы
2) Запуск через docker-compose. Образ с проектом существует на docker-hub в открытом доступе и при запуске compose скачается с него.
   Если необходимо обновить образ то перед этим следует поменять значение prod в main.py на true. (Образ скомпилирован для x86 и не запустится на ARM процессорах от apple)
   
Все доступные ручки:
- /add/csv create_table_from_csv
- /add/str/{table_name} create_table_from_str
- /get/{taxonname} get_data **_(работает по итоговой таблице)_**
- /get-all get_all_data **_(работает по итоговой таблице)_**
- /people/get/{id} get_from_people
- /microorganisms/get/{id} get_from_microorganisms
- /additives/get/{id} get_from_additives
- /people/delete/{id} delete_from_people
- /microorganisms/delete/{id} delete_from_microorganisms
- /additives/delete/{id} delete_from_additives
- /people/update update_people
- /microorganisms/update update_microorganisms
- /additives/update update_additives


Доступ по localhost:8000
