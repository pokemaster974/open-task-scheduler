#!/usr/bin/env python3
import argparse
import yaml
import schedule
import time
import subprocess
import os
import sys

TASKS_FILE = "tasks.yml"

def load_tasks():
    """Charge la configuration des tâches à partir du fichier YAML."""
    if not os.path.exists(TASKS_FILE):
        return []
    with open(TASKS_FILE, "r", encoding="utf-8") as f:
        try:
            data = yaml.safe_load(f)
            if data is None:
                return []
            return data.get("tasks", [])
        except yaml.YAMLError as exc:
            print("Erreur de parsing YAML:", exc)
            return []

def write_tasks(tasks):
    """Sauvegarde la liste de tâches dans le fichier YAML."""
    with open(TASKS_FILE, "w", encoding="utf-8") as f:
        yaml.dump({"tasks": tasks}, f, sort_keys=False, allow_unicode=True)

def list_tasks():
    """Affiche la liste des tâches enregistrées."""
    tasks = load_tasks()
    if not tasks:
        print("Aucune tâche trouvée.")
        return
    print("Tâches programmées :")
    for task in tasks:
        print(f"ID: {task.get('id')}")
        print(f"  Nom       : {task.get('name')}")
        print(f"  Commande  : {task.get('command')} {' '.join(task.get('args', []))}")
        print(f"  Horaire   : {task.get('schedule')} (récurrence: {task.get('recurrence', 'daily')})")
        print("")

def add_task_interactive():
    """Ajoute une nouvelle tâche en demandant les informations à l'utilisateur."""
    tasks = load_tasks()
    id = input("Entrez l'ID unique de la tâche : ").strip()
    if any(task.get("id") == id for task in tasks):
        print("Une tâche avec cet ID existe déjà.")
        return
    name = input("Nom de la tâche : ").strip()
    command = input("Chemin complet du programme/script : ").strip()
    args = input("Arguments (séparés par des espaces, optionnel) : ").split()
    schedule_time = input("Heure d'exécution (format HH:MM, ex: 09:00) : ").strip()
    recurrence = input("Récurrence (daily/weekly, par défaut daily) : ").strip()
    if recurrence == "":
        recurrence = "daily"
    new_task = {
        "id": id,
        "name": name,
        "command": command,
        "args": args,
        "schedule": schedule_time,
        "recurrence": recurrence.lower()
    }
    tasks.append(new_task)
    write_tasks(tasks)
    print("Tâche ajoutée avec succès.")

def remove_task(task_id):
    """Supprime la tâche dont l'ID correspond à task_id."""
    tasks = load_tasks()
    new_tasks = [task for task in tasks if task.get("id") != task_id]
    if len(new_tasks) == len(tasks):
        print("Aucune tâche avec cet ID n'a été trouvée.")
    else:
        write_tasks(new_tasks)
        print("Tâche supprimée avec succès.")

def run_task(task):
    """Exécute la tâche (commande + arguments) et affiche le résultat dans la console."""
    print(f"Exécution de la tâche : {task.get('name')} (ID: {task.get('id')})")
    command = task.get("command")
    args = task.get("args", [])
    try:
        subprocess.run([command] + args, check=True)
        print("Tâche exécutée avec succès.")
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors de l'exécution de la tâche : {e}")
    except Exception as e:
        print(f"Exception : {e}")

def schedule_tasks():
    """Parcourt la liste des tâches et les planifie via la bibliothèque schedule."""
    tasks = load_tasks()
    for task in tasks:
        recurrence = task.get("recurrence", "daily").lower()
        time_str = task.get("schedule")
        if recurrence == "daily":
            try:
                schedule.every().day.at(time_str).do(run_task, task)
                print(f"Tâche '{task.get('name')}' programmée tous les jours à {time_str}.")
            except Exception as e:
                print(f"Erreur dans la programmation de la tâche {task.get('id')}: {e}")
        elif recurrence == "weekly":
            # Pour simplifier, on programme la tâche chaque lundi à l'heure donnée.
            try:
                schedule.every().monday.at(time_str).do(run_task, task)
                print(f"Tâche '{task.get('name')}' programmée chaque lundi à {time_str}.")
            except Exception as e:
                print(f"Erreur dans la programmation de la tâche {task.get('id')}: {e}")
        else:
            print(f"Récurrence non supportée pour la tâche {task.get('id')}: {recurrence}")

def run_scheduler_loop():
    """Lance la boucle principale qui exécute les tâches planifiées en continu."""
    print("Démarrage de l'exécution de l'agenda. Appuyez sur Ctrl+C pour arrêter.")
    schedule_tasks()
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("Arrêt de l'agenda.")

def test_task(task_id):
    """Teste immédiatement une tâche identifiée par son ID."""
    tasks = load_tasks()
    for task in tasks:
        if task.get("id") == task_id:
            print(f"Test de la tâche '{task.get('name')}' (ID: {task_id})")
            run_task(task)
            return
    print("Aucune tâche avec cet ID n'a été trouvée.")

def main():
    parser = argparse.ArgumentParser(description="Gestionnaire de tâches avancé via YAML")
    parser.add_argument("command", choices=["run", "list", "add", "remove", "test"], help="Commande à exécuter")
    parser.add_argument("--id", help="ID de la tâche (pour les commandes remove et test)")
    args = parser.parse_args()

    if args.command == "list":
        list_tasks()
    elif args.command == "add":
        add_task_interactive()
    elif args.command == "remove":
        if not args.id:
            print("Veuillez spécifier --id pour supprimer une tâche.")
            sys.exit(1)
        remove_task(args.id)
    elif args.command == "test":
        if not args.id:
            print("Veuillez spécifier --id pour tester une tâche.")
            sys.exit(1)
        test_task(args.id)
    elif args.command == "run":
        run_scheduler_loop()

if __name__ == "__main__":
    main()
