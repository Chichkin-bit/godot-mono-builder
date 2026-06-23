import subprocess
import os
from pathlib import Path
import shutil

def main():
    # Проверка наличия Git:
    if is_tool_installed(['git', '--version']):
        print("Git успешно найден!")
    else:
        print("Ошибка: Утилита Git не установлена в системе или не добавлена в PATH.")
        return
    
    REPO_URL = 'https://github.com/godotengine/godot.git'
    TARGET_DIR = './godot-source'
    ENCRYPTION_KEY = os.urandom(32).hex()
    
    # Клонирование репозитория:
    if not Path(TARGET_DIR).exists():
        if confirm_action('Начать клонировать репозиторий?'):
            if not clone_repository(REPO_URL, TARGET_DIR, branch='4.7-stable'):
                print("Завершение работы.")
                return
        else:
            print("Завершение работы.")
            return
    else:
        print("Репозиторий успешно найден!")

    # Проверка и установка SCons:
    if is_tool_installed(['scons', '--version']):
        print("SCons успешно найден!")
    else:
        print("SCons не найден. Начинается установка SCons.")
        if not scons_install():
            print("Завершение работы.")
            return
    
    # Создание файлов Glue:
    glue_dir_exists, glue_editor_dir_exists = glue_check()
    if glue_dir_exists and glue_editor_dir_exists:
        print("Файлы Glue успешно найдены!")
    else:
        params = []
        if confirm_action('Начать установку зависимостей?'):
            if confirm_action('Включить поддержку Direct3D 12?'):
                if install_dependency(['python', 'misc/scripts/install_d3d12_sdk_windows.py']):
                    params.append('d3d12=yes')
                else: return
            else:
                params.append('d3d12=no')
            if confirm_action('Включить поддержку AccessKit?'):
                if install_dependency(['python', 'misc/scripts/install_accesskit.py']):
                    params.append('accesskit=yes')
                else: return
            else:
                params.append('accesskit=no')
            if confirm_action('Включить поддержку WinRT?'):
                if install_dependency(['python', 'misc/scripts/install_winrt.py']):
                    params.append('winrt=yes')
                else: return
            else:
                params.append('winrt=no')
        else:
            params.extend(['d3d12=no', 'accesskit=no', 'winrt=no'])
        
        print('Сборка временного исполняемого файла редактора Godot.')
        if not build_godot_editor(params):
            print("Завершение работы.")
            return

        print('Генерация файлов Glue.')
        if not glue_generate():
            print("Завершение работы.")
            return

    # Сборка библиотек:
    if Path('./godot-source/bin/GodotSharp').exists():
        print("Библиотеки успешно найдены!")
    else:
        if not library_generate():
            print("Завершение работы.")
            return
    
    # Генерация шаблона проекта:
    if confirm_action('Начать сборку шаблона проекта?'):
        template_generate(ENCRYPTION_KEY)


def confirm_action(message):
    while True:
        print(message)
        print('y/n')
        user_input = input().casefold()

        if user_input == 'y':
            return True
        elif user_input == 'n':
            return False
        else:
            print(f"Некорректные введенные данные!")


def is_tool_installed(command):
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            encoding='utf-8'
            )
        return result.returncode == 0
    except FileNotFoundError:
        return False


def clone_repository(repo_url, target_dir, *, branch='4.7-stable'):
    os.makedirs(target_dir, exist_ok=True)

    command = [
        'git',
        'clone',
        '--single-branch',
        '-b',
        branch,
        repo_url,
        target_dir
    ]
    try:
        subprocess.run(command, check=True)
        return True
    except subprocess.CalledProcessError as err:
        print(f"Ошибка при клонировании репозитория: {err}")
        return False


def scons_install():
    command = [
        'python',
        '-m',
        'pip',
        'install',
        'scons'
    ]
    try:
        subprocess.run(command, check=True)
        return True
    except subprocess.CalledProcessError as err:
        print(f"Ошибка при установке: {err}")
        return False


def install_dependency(dependency_command):
    source_dir = Path('./godot-source').resolve()
    try:
        subprocess.run(dependency_command, cwd=source_dir, check=True)
        return True
    except subprocess.CalledProcessError as err:
        print(f"Ошибка при установке зависимости: {err}")
        return False
    except FileNotFoundError:
        print(f"Ошибка: Директория {source_dir} не найдена.")
        return False


def build_godot_editor(scons_flags):
    command = [
        'scons',
        'platform=windows',
        'tools=yes',
        'mono_glue=no',
        'target=editor',
        'module_mono_enabled=yes'
    ]

    for flag in scons_flags:
        command.append(flag)
    
    source_dir = Path('./godot-source').resolve()

    try:
        subprocess.run(command, cwd=source_dir, check=True)
        return True
    except subprocess.CalledProcessError as err:
        print(f"Ошибка при сборке временного исполняемого файла редактора Godot: {err}")
        return False
    except FileNotFoundError:
        print(f"Ошибка: Директория {source_dir} или утилита scons не найдены.")
        return False


def glue_check():
    glue = Path('./godot-source/modules/mono/glue/GodotSharp/GodotSharp/Generated').resolve()
    glue_editor = Path('./godot-source/modules/mono/glue/GodotSharp/GodotSharpEditor/Generated').resolve()
    return glue.is_dir(), glue_editor.is_dir()


def glue_generate():
    source_dir = Path('./godot-source').resolve()
    godot_exe_path = Path('./godot-source/bin/godot.windows.editor.x86_64.mono.exe').resolve()
    try:
        subprocess.run([godot_exe_path, '--headless', '--generate-mono-glue', 'modules/mono/glue'], cwd=source_dir, check=True)
        return True
    except subprocess.CalledProcessError as err:
        print(f"Ошибка при создании файлов Glue: {err}")
        return False


def library_generate():
    source_dir = Path('./godot-source').resolve()
    command = [
        'python',
        './modules/mono/build_scripts/build_assemblies.py',
        '--godot-output-dir=./bin',
        '--godot-platform=windows'
    ]
    try:
        subprocess.run(command, cwd=source_dir, check=True)
        return True
    except subprocess.CalledProcessError as err:
        print(f"Ошибка сборки библиотек: {err}")
        return False


def template_generate(encrypt_key):
    dir_path = './godot-source/bin/obj'
    source_dir = Path('./godot-source').resolve()

    try:
        shutil.rmtree(dir_path)
        print(f"Директория {dir_path} успешно удалена!")
    except FileNotFoundError:
        print(f"Директория {dir_path} не найдена.")
    except PermissionError:
        print(f"Нет прав для удаления директории {dir_path}.")

    curr_env = os.environ.copy()
    curr_env['SCRIPT_AES256_ENCRYPTION_KEY'] = encrypt_key
    command = [
        'scons',
        'platform=windows',
        'target=template_release',
        'module_mono_enabled=yes'
    ]
    try:
        subprocess.run(command, cwd=source_dir, env=curr_env, check=True)
        print(f"Сборка шаблона проекта успешно завершена!\nКлюч шифрования для шаблона проекта: {encrypt_key}")
    except subprocess.CalledProcessError as err:
        print(f"Ошибка при генерации шаблона: {err}")


main()