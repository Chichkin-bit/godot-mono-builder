import subprocess
import os
from pathlib import Path
import shutil

def main():
    # Проверка наличия Git:
    if is_tool_installed(['git', '--version']):
        print("Git found successfully!\nGit успешно найден!")
    else:
        print("Error: Git is not installed on the system or not added to PATH.\nОшибка: Утилита Git не установлена в системе или не добавлена в PATH.")
        return
    
    REPO_URL = 'https://github.com/godotengine/godot.git'
    TARGET_DIR = './godot-source'
    ENCRYPTION_KEY = os.urandom(32).hex()
    
    # Клонирование репозитория:
    if not Path(TARGET_DIR).exists():
        if confirm_action('Start cloning the repository?\nНачать клонировать репозиторий?'):
            if not clone_repository(REPO_URL, TARGET_DIR, branch='4.7-stable'):
                print("Exiting.\nЗавершение работы.")
                return
        else:
            print("Exiting.\nЗавершение работы.")
            return
    else:
        print("Repository found successfully!\nРепозиторий успешно найден!")

    # Проверка и установка SCons:
    if is_tool_installed(['scons', '--version']):
        print("SCons found successfully!\nSCons успешно найден!")
    else:
        print("SCons not found. Starting SCons installation.\nSCons не найден. Начинается установка SCons.")
        if not scons_install():
            print("Exiting.\nЗавершение работы.")
            return
    
    # Создание файлов Glue:
    glue_dir_exists, glue_editor_dir_exists = glue_check()
    if glue_dir_exists and glue_editor_dir_exists:
        print("Glue files found successfully!\nФайлы Glue успешно найдены!")
    else:
        params = []
        if confirm_action('Start installing dependencies?\nНачать установку зависимостей?'):
            if confirm_action('Include Direct3D 12 support?\nВключить поддержку Direct3D 12?'):
                if install_dependency(['python', 'misc/scripts/install_d3d12_sdk_windows.py']):
                    params.append('d3d12=yes')
                else: return
            else:
                params.append('d3d12=no')
            if confirm_action('Include AccessKit support?\nВключить поддержку AccessKit?'):
                if install_dependency(['python', 'misc/scripts/install_accesskit.py']):
                    params.append('accesskit=yes')
                else: return
            else:
                params.append('accesskit=no')
            if confirm_action('Include WinRT support?\nВключить поддержку WinRT?'):
                if install_dependency(['python', 'misc/scripts/install_winrt.py']):
                    params.append('winrt=yes')
                else: return
            else:
                params.append('winrt=no')
        else:
            params.extend(['d3d12=no', 'accesskit=no', 'winrt=no'])
        
        print('Building temporary Godot editor executable.\nСборка временного исполняемого файла редактора Godot.')
        if not build_godot_editor(params):
            print("Exiting.\nЗавершение работы.")
            return

        print('Generating Glue files.\nГенерация файлов Glue.')
        if not glue_generate():
            print("Exiting.\nЗавершение работы.")
            return

    # Сборка библиотек:
    if Path('./godot-source/bin/GodotSharp').exists():
        print("Libraries found successfully!\nБиблиотеки успешно найдены!")
    else:
        if not library_generate():
            print("Exiting.\nЗавершение работы.")
            return
    
    # Генерация шаблона проекта:
    if confirm_action('Start building the project template?\nНачать сборку шаблона проекта?'):
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
            print("Invalid input!\nНекорректные введенные данные!")


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
        print(f"Error cloning repository: {err}\nОшибка при клонировании репозитория: {err}")
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
        print(f"Error installing scons: {err}\nОшибка при установке scons: {err}")
        return False


def install_dependency(dependency_command):
    source_dir = Path('./godot-source').resolve()
    try:
        subprocess.run(dependency_command, cwd=source_dir, check=True)
        return True
    except subprocess.CalledProcessError as err:
        print(f"Error installing dependency: {err}\nОшибка при установке зависимости: {err}")
        return False
    except FileNotFoundError:
        print(f"Error: Directory {source_dir} not found.\nОшибка: Директория {source_dir} не найдена.")
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
        print(f"Error building temporary Godot editor executable: {err}\nОшибка при сборке временного исполняемого файла редактора Godot: {err}")
        return False
    except FileNotFoundError:
        print(f"Error: Directory {source_dir} or scons utility not found.\nОшибка: Директория {source_dir} или утилита scons не найдены.")
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
        print(f"Error generating Glue files: {err}\nОшибка при создании файлов Glue: {err}")
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
        print(f"Error building libraries: {err}\nОшибка сборки библиотек: {err}")
        return False


def template_generate(encrypt_key):
    dir_path = './godot-source/bin/obj'
    source_dir = Path('./godot-source').resolve()

    try:
        shutil.rmtree(dir_path)
        print(f"Directory {dir_path} removed successfully!\nДиректория {dir_path} успешно удалена!")
    except FileNotFoundError:
        print(f"Directory {dir_path} not found.\nДиректория {dir_path} не найдена.")
    except PermissionError:
        print(f"Permission denied to remove directory {dir_path}.\nНет прав для удаления директории {dir_path}.")

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
        print(f"Project template build completed successfully!\nEncryption key for the project template:\nСборка шаблона проекта успешно завершена!\nКлюч шифрования для шаблона проекта:")
        print(encrypt_key)
    except subprocess.CalledProcessError as err:
        print(f"Error generating template: {err}\nОшибка при генерации шаблона: {err}")


main()