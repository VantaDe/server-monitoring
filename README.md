
### README.md

# Server-Monitoring mit Flask

Dieses Projekt ist eine einfache Webanwendung, die Systeminformationen wie CPU-Auslastung, RAM, SSD-Nutzung, Uptime und Netzwerkleistung in Echtzeit anzeigt. Ein integrierter Speedtest kann manuell gestartet werden, um die Netzwerkgeschwindigkeit zu messen.

## Voraussetzungen

Stellen Sie sicher, dass **Python 3** auf Ihrem System installiert ist.
Sie müssen die folgenden Python-Bibliotheken installieren:

```bash
pip install flask psutil speedtest-cli
```

## Installation

1.  Speichern Sie den bereitgestellten Code in einer Datei namens `app.py`.
2.  Installieren Sie die notwendigen Python-Pakete wie oben beschrieben.

## Ausführung

### Windows

Um die Anwendung unter Windows auszuführen, öffnen Sie die Eingabeaufforderung oder PowerShell im Verzeichnis, in dem Sie die Datei `app.py` gespeichert haben, und führen Sie den folgenden Befehl aus:

```bash
python app.py
```

Die Anwendung wird auf `http://localhost:5000` verfügbar sein.

### Linux

Für Linux ist der Prozess ähnlich. Öffnen Sie ein Terminal, navigieren Sie zum Verzeichnis der Datei und führen Sie den Befehl aus:

```bash
python3 app.py
```

Die Anwendung wird auf `http://<Ihre-Server-IP>:5000` verfügbar sein.

-----

## Einrichtung als Systemdienst (systemd) unter Linux

Um sicherzustellen, dass die Anwendung auch nach einem Neustart automatisch gestartet wird, können Sie einen `systemd`-Dienst erstellen.

1.  **Erstellen Sie ein Startskript (optional, aber empfohlen):**
    Erstellen Sie eine Datei `start_app.sh` im selben Verzeichnis wie `app.py` mit folgendem Inhalt:

    ```bash
    #!/bin/bash
    cd /pfad/zu/ihrem/projektverzeichnis
    python3 app.py
    ```

    Stellen Sie sicher, dass das Skript ausführbar ist:

    ```bash
    chmod +x start_app.sh
    ```

2.  **Erstellen Sie eine Systemd-Dienstdatei:**
    Erstellen Sie eine neue Dienstdatei unter `/etc/systemd/system/` mit einem Editor wie `nano`:

    ```bash
    sudo nano /etc/systemd/system/server_monitor.service
    ```

3.  **Fügen Sie den folgenden Inhalt in die Datei ein:**
    Passen Sie `User`, `Group` und den `ExecStart` Pfad an Ihr System an.

    ```ini
    [Unit]
    Description=Flask Server Monitoring App
    After=network.target

    [Service]
    User=<Ihr-Benutzername>
    Group=<Ihre-Gruppe>
    WorkingDirectory=/pfad/zu/ihrem/projektverzeichnis
    ExecStart=/pfad/zu/ihrem/projektverzeichnis/start_app.sh
    Restart=always

    [Install]
    WantedBy=multi-user.target
    ```

    **Hinweis:** Ersetzen Sie `<Ihr-Benutzername>`, `<Ihre-Gruppe>` und `/pfad/zu/ihrem/projektverzeichnis` durch die korrekten Werte für Ihren Server.

4.  **Dienst aktivieren und starten:**
    Nachdem Sie die Datei gespeichert haben, aktivieren und starten Sie den Dienst mit diesen Befehlen:

    ```bash
    sudo systemctl daemon-reload
    sudo systemctl enable server_monitor.service
    sudo systemctl start server_monitor.service
    ```

Sie können den Status des Dienstes jederzeit mit dem Befehl `sudo systemctl status server_monitor.service` überprüfen.

Der zugang zur Website wird über die IP gewährt sprich http://server-ip:5000
Port wurde 5000 gewählt 
