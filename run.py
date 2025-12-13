from app import create_app

app = create_app()

if __name__ == "__main__":
    # debug True for local development
    app.run(debug=True, port=5000)
