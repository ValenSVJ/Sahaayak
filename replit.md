# Sahaayak - Vendor Club Management Platform

## Overview

Sahaayak is a Flask-based web application that connects vendors with wholesalers for fresh produce and ingredient sourcing. The platform facilitates vendor clubs, product ordering, and includes AI-powered features for enhanced user experience. The system manages vendor registration, wholesaler partnerships, product catalogs, and order processing with a focus on the fresh produce supply chain.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Backend Architecture
- **Framework**: Flask (Python web framework)
- **Database**: SQLite with raw SQL queries (no ORM)
- **Authentication**: Session-based authentication with werkzeug password hashing
- **File Handling**: Werkzeug secure filename utilities for document uploads
- **AI Integration**: Google Gemini AI for enhanced features

### Frontend Architecture
- **Template Engine**: Jinja2 (Flask's default)
- **CSS Framework**: Bootstrap 5.3.0
- **Icons**: Font Awesome 6.4.0
- **Fonts**: Google Fonts (Inter)
- **JavaScript**: Vanilla JS with Web Speech API for voice search

### Key Technologies
- **Python Flask**: Core web framework
- **SQLite**: Lightweight database for development
- **Bootstrap**: Responsive UI framework
- **Google Gemini AI**: AI-powered features
- **HTML5 Speech Recognition**: Voice search functionality

## Key Components

### Database Schema
The application uses SQLite with the following core tables:

1. **Vendors Table**
   - User registration and authentication
   - Location and approval status tracking
   - Contact information management

2. **Wholesalers Table**
   - Business registration with document verification
   - Performance metrics (trust_score, response_rate, delivery_rate)
   - Shop details and sourcing information

3. **Products Table**
   - Product catalog with categories
   - Stock management and pricing
   - Image uploads and product descriptions

4. **Orders Table**
   - Order processing and status tracking
   - Vendor-wholesaler transaction records
   - Quantity and delivery management

### Authentication System
- **Session Management**: Flask sessions for user state
- **Password Security**: Werkzeug password hashing
- **Role-based Access**: Separate authentication for vendors, wholesalers, and admin
- **Admin Dashboard**: Centralized management interface

### File Upload System
- **Document Storage**: Static file handling for licenses and ID documents
- **Product Images**: Image upload for product catalogs
- **Security**: Secure filename processing and file type validation
- **Storage Location**: `/static/uploads` directory

## Data Flow

### User Registration Flow
1. Vendor/Wholesaler submits registration form
2. Documents uploaded to static storage
3. Admin approval process through dashboard
4. Account activation and login access

### Product Management Flow
1. Approved wholesalers add products to catalog
2. Product information stored with categories and stock levels
3. Vendors browse categorized product listings
4. Search and filtering capabilities

### Ordering Process
1. Vendors select products and quantities
2. Orders created with wholesaler assignment
3. Order status tracking through dashboard
4. Communication between vendors and wholesalers

## External Dependencies

### AI Integration
- **Google Gemini AI**: API integration for enhanced features
- **Configuration**: Environment variable-based API key management
- **Use Cases**: Likely for product recommendations and search enhancement

### Frontend Libraries
- **Bootstrap 5.3.0**: CDN-hosted responsive framework
- **Font Awesome 6.4.0**: Icon library via CDN
- **Google Fonts**: Typography enhancement

### Development Tools
- **python-dotenv**: Environment variable management
- **Werkzeug**: WSGI utilities and security functions

## Deployment Strategy

### Environment Configuration
- **Secret Key**: Configurable via environment variables
- **API Keys**: Secure storage of Gemini AI credentials
- **File Upload Limits**: Configurable maximum file sizes
- **Database**: SQLite for development, scalable to PostgreSQL for production

### File Structure
- **Static Assets**: Organized in `/static` directory (CSS, JS, uploads)
- **Templates**: Jinja2 templates in `/templates` directory
- **Configuration**: Environment-based configuration with fallback defaults

### Security Considerations
- **Password Hashing**: Werkzeug security functions
- **File Upload Security**: Secure filename handling and type validation
- **Session Management**: Flask session security
- **API Key Protection**: Environment variable storage

### Scalability Considerations
- **Database**: SQLite suitable for development, can migrate to PostgreSQL
- **File Storage**: Local storage for development, can move to cloud storage
- **AI Services**: External API integration for scalable AI features
- **Caching**: Framework prepared for caching implementation

The application follows a traditional MVC pattern with Flask, providing a solid foundation for a vendor-wholesaler marketplace with modern features like voice search and AI integration.