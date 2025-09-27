#!/usr/bin/env python3
"""
Whisper Model Upgrade Script
Easily switch between different Whisper models for better accuracy
"""

import os
import sys
from pathlib import Path


def update_env_model(model_size):
    """Update the .env file with new model size"""
    env_path = Path(__file__).parent / ".env"

    if not env_path.exists():
        print("❌ .env file not found")
        return False

    # Read current .env content
    with open(env_path, "r") as f:
        lines = f.readlines()

    # Update or add WHISPER_MODEL_SIZE
    updated = False
    new_lines = []

    for line in lines:
        if line.startswith("WHISPER_MODEL_SIZE="):
            new_lines.append(f"WHISPER_MODEL_SIZE={model_size}\n")
            updated = True
        else:
            new_lines.append(line)

    # If not found, add it
    if not updated:
        new_lines.append(
            f"\n# Whisper Model Configuration\nWHISPER_MODEL_SIZE={model_size}\n"
        )

    # Write back to file
    with open(env_path, "w") as f:
        f.writelines(new_lines)

    print(f"✅ Updated .env file: WHISPER_MODEL_SIZE={model_size}")
    return True


def show_model_info():
    """Show information about available models"""
    models = {
        "tiny": {
            "size": "39 MB",
            "speed": "⚡ Fastest",
            "accuracy": "😐 Good",
            "use_case": "Quick testing, very low-end devices",
        },
        "base": {
            "size": "74 MB",
            "speed": "🚀 Fast",
            "accuracy": "😊 Very Good",
            "use_case": "General use, good balance",
        },
        "small": {
            "size": "244 MB",
            "speed": "🐌 Medium",
            "accuracy": "😍 Excellent",
            "use_case": "Better accuracy, moderate hardware",
        },
        "medium": {
            "size": "769 MB",
            "speed": "🐢 Slow",
            "accuracy": "🤩 Excellent",
            "use_case": "🎯 RECOMMENDED for Hindi/multilingual",
        },
        "large": {
            "size": "1550 MB",
            "speed": "🦕 Slowest",
            "accuracy": "🏆 Best",
            "use_case": "Maximum accuracy, powerful hardware",
        },
        "large-v2": {
            "size": "1550 MB",
            "speed": "🦕 Slowest",
            "accuracy": "🏆 Best",
            "use_case": "Latest improvements",
        },
        "large-v3": {
            "size": "1550 MB",
            "speed": "🦕 Slowest",
            "accuracy": "👑 Best",
            "use_case": "Newest model, cutting-edge",
        },
    }

    print("🎤 Available Whisper Models:")
    print("=" * 60)

    for model, info in models.items():
        print(f"\n📦 {model.upper()}")
        print(f"   Size: {info['size']}")
        print(f"   Speed: {info['speed']}")
        print(f"   Accuracy: {info['accuracy']}")
        print(f"   Use Case: {info['use_case']}")


def main():
    """Main upgrade function"""
    print("🚀 Whisper Model Upgrade Tool")
    print("=" * 40)

    if len(sys.argv) < 2:
        print("\n📋 Usage:")
        print("  python upgrade_model.py <model_size>")
        print("  python upgrade_model.py info")
        print("\n💡 Examples:")
        print("  python upgrade_model.py medium    # Upgrade to medium model")
        print("  python upgrade_model.py large     # Upgrade to large model")
        print("  python upgrade_model.py info      # Show model information")
        return

    command = sys.argv[1].lower()

    if command == "info":
        show_model_info()
        print("\n🎯 Recommendations:")
        print("  • For Hindi/Urdu: medium or large")
        print("  • For English only: small or base")
        print("  • For multilingual: medium or large")
        print("  • For maximum accuracy: large-v3")
        return

    # Validate model size
    valid_models = ["tiny", "base", "small", "medium", "large", "large-v2", "large-v3"]
    if command not in valid_models:
        print(f"❌ Invalid model: {command}")
        print(f"✅ Valid models: {', '.join(valid_models)}")
        return

    # Update .env file
    if update_env_model(command):
        print(f"\n🎯 Next steps:")
        print(f"1. Restart the voice server:")
        print(f"   python voice_server.py")
        print(f"2. The new {command} model will be downloaded on first use")
        print(f"3. Expect better accuracy with the upgraded model!")

        if command in ["medium", "large", "large-v2", "large-v3"]:
            print(f"\n⚠️  Note: {command} model is larger and may take longer to load")
            print(f"   But you'll get much better accuracy, especially for Hindi!")


if __name__ == "__main__":
    main()
