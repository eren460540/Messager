from http.client import HTTPSConnection
import sys
import json
from time import sleep
from random import choice, random, uniform

file = open("info.txt")
text = file.read().splitlines()

if len(sys.argv) > 1 and sys.argv[1] == "--setall" and input("Configure bot? (y/n)") == "y":
    file.close()
    file = open("info.txt", "w")
    text = []
    text.append(input("User agent: "))
    text.append(input("Discord token: "))

    for parameter in text:
        file.write(parameter + "\n")

    file.close()
    exit()
elif len(sys.argv) > 1 and sys.argv[1] == "--help":
    print("Showing help for discord-auto-message")
    print("Usage:")
    print("  'python3 bot.py'               :  Runs the autotyper with task configuration.")
    print("  'python3 bot.py --setall'      :  Configure authentication (User Agent and Token).")
    print("  'python3 bot.py --help'        :  Show help")
    exit()

if len(text) != 2:
    print(
        "An error was found inside the user information file. Run the script with the 'Set All' flag ('python3 bot.py --setall') to reconfigure.")
    exit()

if len(sys.argv) > 1:
    exit()

user_agent = text[0]
token = text[1]

messages_list = [
    "Yoo",
    "wsp yall",
    "dang ts lwk dead",
    "holyy",
]


def get_connection():
    return HTTPSConnection("discordapp.com", 443)


def send_message(conn, channel_id, message_data):
    """Send a message and return the message ID if successful"""
    try:
        header_data = {
            "content-type": "application/json",
            "user-agent": user_agent,
            "authorization": token,
            "host": "discordapp.com",
        }
        
        conn.request("POST", f"/api/v6/channels/{channel_id}/messages", message_data, header_data)
        resp = conn.getresponse()
        resp_text = resp.read().decode('utf-8')

        if 199 < resp.status < 300:
            print("✓ Message sent!")
            try:
                resp_json = json.loads(resp_text)
                return resp_json.get('id')  # Return message ID for deletion
            except:
                return None
        else:
            sys.stderr.write(f"✗ Received HTTP {resp.status}: {resp.reason}\n")
            return None

    except Exception as e:
        sys.stderr.write(f"✗ Failed to send message: {e}\n")
        return None


def delete_message(conn, channel_id, message_id):
    """Delete a previously sent message"""
    try:
        header_data = {
            "content-type": "application/json",
            "user-agent": user_agent,
            "authorization": token,
            "host": "discordapp.com",
        }
        
        conn.request("DELETE", f"/api/v6/channels/{channel_id}/messages/{message_id}", "", header_data)
        resp = conn.getresponse()
        resp.read()

        if 199 < resp.status < 300:
            print("✓ Previous message deleted (anti-detect mode)")
            return True
        else:
            sys.stderr.write(f"✗ Failed to delete message: HTTP {resp.status}\n")
            return False

    except Exception as e:
        sys.stderr.write(f"✗ Failed to delete message: {e}\n")
        return False


def run_task(channel_url, channel_id, num_messages, anti_detect):
    """Run a single task (send messages to one channel)"""
    print(f"\n{'='*60}")
    print(f"Task started for channel: {channel_url}")
    print(f"Anti-detect mode: {'ON' if anti_detect else 'OFF'}")
    print(f"{'='*60}\n")

    sent_messages = set()
    last_message_id = None

    for i in range(num_messages):
        # Choose a random message that hasn't been sent recently
        while True:
            random_message = choice(messages_list)
            if random_message not in sent_messages:
                sent_messages.add(random_message)
                # Keep only last 3 to allow some repetition after cycling
                if len(sent_messages) > 3:
                    sent_messages.pop()
                break

        # Random delay between 2-5 minutes
        delay = uniform(120, 300)  # 120-300 seconds = 2-5 minutes
        
        # Send message
        conn = get_connection()
        message_data = json.dumps({
            "content": random_message,
            "tts": "false",
        })
        
        message_id = send_message(conn, channel_id, message_data)
        
        # Delete previous message if anti-detect is on and we have a previous message
        if anti_detect and last_message_id:
            sleep(0.5)  # Small delay before deletion
            conn2 = get_connection()
            delete_message(conn2, channel_id, last_message_id)
            conn2.close()
        
        last_message_id = message_id
        
        # Calculate and display remaining time
        remaining_messages = num_messages - i - 1
        remaining_time = remaining_messages * delay / 60  # Convert to minutes
        
        print(f"Message {i + 1}/{num_messages}: '{random_message}'")
        print(f"Next message in {delay:.1f}s ({delay/60:.2f}m)")
        if remaining_messages > 0:
            print(f"Estimated time to complete: {remaining_time:.1f} minutes\n")
        
        conn.close()
        
        if remaining_messages > 0:
            sleep(delay)

    print(f"\n✓ Task complete! {num_messages} messages sent to {channel_url}\n")


def main():
    print("="*60)
    print("Discord Auto-Message Sender")
    print("="*60)
    
    # Ask for number of tasks
    try:
        num_tasks = int(input("\nHow many tasks? "))
    except ValueError:
        print("Invalid input. Please enter a number.")
        return
    
    if num_tasks < 1:
        print("Must have at least 1 task.")
        return
    
    # Collect all task configurations
    tasks = []
    for task_num in range(num_tasks):
        print(f"\n--- Task {task_num + 1} Configuration ---")
        channel_url = input("Discord channel URL: ").strip()
        channel_id = input("Discord channel ID: ").strip()
        
        try:
            num_messages = int(input("Number of messages to send: "))
            if num_messages < 1:
                print("Must send at least 1 message.")
                return
        except ValueError:
            print("Invalid input. Please enter a number.")
            return
        
        anti_detect = input("Anti-detect mode? (y/n): ").lower() == "y"
        
        tasks.append({
            "channel_url": channel_url,
            "channel_id": channel_id,
            "num_messages": num_messages,
            "anti_detect": anti_detect,
        })
    
    # Run all tasks
    print("\n" + "="*60)
    print(f"Starting {num_tasks} task(s)...")
    print("="*60)
    
    for idx, task in enumerate(tasks, 1):
        print(f"\n[Task {idx}/{num_tasks}]")
        run_task(
            task["channel_url"],
            task["channel_id"],
            task["num_messages"],
            task["anti_detect"]
        )
        
        # Wait between tasks if there are more
        if idx < num_tasks:
            print("Waiting 30 seconds before next task...\n")
            sleep(30)
    
    print("\n" + "="*60)
    print("✓ All tasks complete!")
    print("="*60)


if __name__ == '__main__':
    main()
