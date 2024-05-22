
# Punctual

Punctual is a Python project that ensures you are never late by accurately calculating the total duration of your daily activities. Input your tasks, and this tool will provide you with the total time needed, helping you plan your schedule efficiently.

## Features

- Input a list of activities with their respective durations.
- Calculate the total time required to complete all activities.
- Easy-to-use command-line interface.
- Customizable for different time units (minutes, hours).

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Examples](#examples)
- [Contributing](#contributing)
- [License](#license)

## Installation

To get started with Punctual, clone the repository and install the necessary dependencies.

```bash
git clone https://github.com/JustNello/punctual
cd punctual
pip install -r requirements.txt
```

## Usage

1. **Prepare your list of activities**: Create a JSON file (`activities.json`) with your activities and their durations.

```json
{
    "activities": [
        {"name": "Breakfast", "duration": 30},
        {"name": "Commute", "duration": 45},
        {"name": "Work", "duration": 480},
        {"name": "Gym", "duration": 60},
        {"name": "Dinner", "duration": 45}
    ]
}
```

2. **Run the script**: Use the command-line interface to input your activities file and get the total duration.

```bash
python calculate_time.py activities.json
```

3. **View the result**: The script will output the total time required for all activities.

```bash
Total time required: 660 minutes
```

## Examples

Here are a few examples of how you can use Punctual:

- **Example 1**: Basic usage with a simple activities list.
- **Example 2**: Customizing the time unit to hours.
- **Example 3**: Integrating with calendar applications.

### Example 1: Basic Usage

```bash
python calculate_time.py activities.json
```

**Output:**
```
Total time required: 660 minutes
```

### Example 2: Time Unit Customization

Modify the script to display the total time in hours.

```bash
python calculate_time.py activities.json --unit hours
```

**Output:**
```
Total time required: 11 hours
```

## Contributing

We welcome contributions! If you'd like to contribute, please fork the repository and use a feature branch. Pull requests are warmly welcome.

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature-name`).
3. Commit your changes (`git commit -am 'Add some feature'`).
4. Push to the branch (`git push origin feature-name`).
5. Create a new Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

For any questions or suggestions, feel free to open an issue or contact us at yourname@example.com.

Happy scheduling!
