An automated Python script for building a custom version of the **Godot Engine (4.7)** with **C# (Mono)** support on Windows, featuring automatic export template encryption.

## ✨ Key Features

* **Dependency Management:** Automatically detects or prompts to install `SCons`, as well as optional SDKs (Direct3D 12, AccessKit, WinRT).
* **Security:** Automatically generates a 32-byte AES key to protect project scripts and embeds it into the release export template.
* Currently, creating release templates is only supported for Windows!

## 🛠 System Requirements

Before running the script, ensure that your Windows system has the following installed:
1. **Python 3.x** (must be added to `PATH`).
2. **Git**.
3. **.NET SDK** (required for building Mono/C# modules).
4. **Visual Studio** with a C++ compiler installed (must be added to `PATH`).

## 🚀 How to Run

1. Clone this repository to your computer.
2. Run the main script: *python main.py*
3. Follow the console prompts (y/n) to select the required build components.

## 💎 Upon Template Creation Completion:

1. You will receive a 32-byte AES key and the export template in the `bin` folder.
2. In the Godot editor, navigate to: **Project -> Export -> Encryption**.
3. Enable: **Encrypt Exported PCK**.
4. Set `*.*` in the field: **Filters to include files/folders**.
5. Paste the generated key into the field: **Encryption Key**.
6. Go to the export options and specify the path to your release export template.

## ⚙️ Steps Automated by the Script:
* Checking for installed `git` and `scons` on the system.
* Cloning the `4.7-stable` branch from the official Godot repository.
* Building a temporary `4.7-stable` editor executable.
* Generating C# Glue files.
* Building the final GodotSharp managed libraries.
* Building the release export template with a unique encryption key.

## ‼️ What's Next?
Currently, building templates is only supported for the Windows target platform. I plan to implement export template selection for other platforms in the future.

[[Читать на русском языке](README.ru.md)]
