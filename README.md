# TODO API with Django REST Framework

![Django REST Framework](https://img.shields.io/badge/DJANGO-REST-ff1709?style=for-the-badge&logo=django&logoColor=white&color=ff1709&labelColor=gray)
![Postgres](https://img.shields.io/badge/postgres-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/redis-%23DD0031.svg?style=for-the-badge&logo=redis&logoColor=white)
![JWT](https://img.shields.io/badge/JWT-black?style=for-the-badge&logo=JSON%20web%20tokens)

A robust TODO API built with Django REST Framework featuring JWT authentication with OTP via SMS, comprehensive task management with steps, tags, and contacts, and full admin integration.

## Features

- **Secure Authentication**:
  - JWT authentication
  - OTP login via SMS
  - Single endpoint for registration/login
  - User profile management

- **Task Management**:
  - Full CRUD operations for Tasks
  - Step management for breaking down tasks
  - Tag system for organization
  - Contact management for collaboration

- **Technical Highlights**:
  - 164 comprehensive pytest tests
  - Clean, modular OOP design with custom mixins
  - Rate limiting for API protection
  - Beautiful Django admin interface with Jazzmin
  - Complete Swagger documentation (drf-spectacular)
  - PostgreSQL database backend
  - Redis for caching and rate limiting

## API Endpoints

| Endpoint               | Description                          |
|------------------------|--------------------------------------|
| `api/v2/auth/`         | User authentication and registration |
| `api/v2/tasks/`        | Task management                      |
| `api/v2/steps/`        | Step management for tasks            |
| `api/v2/tags/`         | Tag management                       |
| `api/v2/contacts/`     | Contact management                   |
| `api/v2/docs/`         | Interactive API documentation        |
| `api/v2/schema/`       | API schema (OpenAPI)                 |

All endpoints support GET, POST, PATCH, and DELETE methods where applicable.

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/HjtDev/TODO-API/
   cd TODO-API
   ```

2. **Set up environment**:
    - Create a `.env` file in the project root with your sensitive data
    - Example `.env` structure:
      ```
      SECRET_KEY=your_django_secret_key
      ALLOWED_HOSTS=your_allowed_hosts
      DEBUG=True
      DB_NAME=your_db_name
      DB_USER=your_db_user
      DB_PASSWORD=your_db_password
      REDIS_LOCATION=your_redis_url
      ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Database setup**:
    - Create a PostgreSQL database with the name specified in your `.env` file
    - Run migrations:
      ```bash
      python manage.py migrate
      ```

5. **Redis configuration**:
    - Install and run Redis server
    - Ensure the Redis URL in `.env` is correct

## Running the Project

1. Start the development server:
   ```bash
   python manage.py runserver
   ```

2. Access the API at `http://localhost:8000/api/v2/docs/` for interactive documentation

## Testing

The project includes 164 tests written with pytest. To run them:

```bash
pytest
```

Test configuration is in `pytest.ini`.

## Admin Interface

Access the admin interface at `http://localhost:8000/admin/` after creating a superuser:

```bash
python manage.py createsuperuser
```

## Project Structure

The code is organized in a modular OOP fashion with:
- Custom mixins for reusable functionality
- Dedicated OTP models for authentication
- Separate apps for each feature (tasks, steps, tags, contacts)
- Clean separation of concerns