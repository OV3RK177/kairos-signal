import ollama
import sys
import os

MODEL = "kimi-k2-thinking:cloud"
BRIEFING_FILE = "briefing_v28.md"

def load_context():
    if os.path.exists(BRIEFING_FILE):
        with open(BRIEFING_FILE, "r") as f:
            return f.read()
    return "You are Kairos Signal core. Persona: Tin Man."

def main():
    system_context = load_context()
    
    history = [
        {'role': 'system', 'content': system_context}
    ]

    print(f"// KAIROS SIGNAL ONLINE // MODEL: {MODEL}")
    print("// CTRL+C to Terminate\n")

    while True:
        try:
            user_input = input("USER > ")
            if not user_input:
                continue
            if user_input.lower() in ['exit', 'quit']:
                break
            
            history.append({'role': 'user', 'content': user_input})

            print(f"\nKAIROS > ", end='', flush=True)
            
            stream = ollama.chat(
                model=MODEL,
                messages=history,
                stream=True,
            )

            full_response = ""
            for chunk in stream:
                content = chunk['message']['content']
                full_response += content
                print(content, end='', flush=True)
            
            print("\n")
            
            history.append({'role': 'assistant', 'content': full_response})
            
        except KeyboardInterrupt:
            print("\n// SESSION TERMINATED")
            sys.exit(0)
        except Exception as e:
            print(f"\nERROR: {e}")

if __name__ == "__main__":
    main()
