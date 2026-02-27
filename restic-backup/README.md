# RESTIC BACKUP FROM WINDOWS TO LINUX (by SFTP)

## Подготовка Linux хоста

1. **Конфигурация sshd**  
Переходим в директорию с конфигами - `cd /etc/ssh/sshd_config.d/`  
Создаем файл с расширением `.conf`  
Содержание конфиг файла:  

```bash
Match User <username> # Имя пользователя. Можно так же Match Group для конфигурации всей группы 
    ChrootDirectory <directory> # Корневая папка для подключаемого пользователя
    ForceCommand internal-sftp # Принудительно переводит пользователя из ssh в sftp соединение
    AllowTcpForwarding no # Запрет на TCP-туннели
    PasswordAuthentication no # Запретить вход по паролю
    PubkeyAuthentication yes # Аутенфикация через публичный ключ
```  

Так же проверяем, чтоб в файле `etc/ssh/sshd_config` присутсовала строка `Include etc/ssh/sshd_config.d/*.conf`  
2. **Настройка SFTP-директории**  
Для примера будет директория в корне системы - `/share/sftp/backup`  
Для `/share/sftp/`: (Она будет корнем для клиента)  
    `chown root:root /share /share/sftp`  
    `chmod 0755 /share /share/sftp`  
Для `/share/sftp/backup/`:  (Делаем writable директорию)
    `chown <user>:<user_hroup> /share/sftp/backup`  
    `chmod 0755 /share/sftp/backup`  
3. **Настройка пользователя**  
Вставляем содержимое публичного ключа в файл - `/home/<username>/.ssh/authorized_keys`

В самом конце - `sudo systemctl restart sshd`

## Подготовка Windows хоста

1. **Создание SSH-ключа**  

```powershell
# restic это имя файла ключа, а -C - комментарий
ssh-keygen -t edd25519 -f "$env:USERPROFILE\.ssh\restic" -C "restic-backup" 
```

passphrase оставляем пустым  

Открываем файл user\.ssh\config  

```txt
Host <name> # Имя Linux хоста
  HostName <ip> # ip адрес
  User <username> # под каким пользователем подключаемся
  PreferredAuthentications publickey
  IdentityFile C:\Users\<username>\.ssh\restic
  IdentitiesOnly yes
  BatchMode yes
```  

Сохраняем  

## Бекап

1. **Инициализируем репозиторий**  
`.\restic.exe -r "sftp:<username>@<hostname>:/backup/" --password-file=.\pass.txt init`  
pass.txt - файл с паролем для репозитория. Без пробелов и отступов. Не потеряйте его!  

2. **Делаем бекап**  
`.\restic.exe -r "sftp:<username>@<hostname>:/backup/" backup <Путь до директории, которую хотим забекапить>`  
