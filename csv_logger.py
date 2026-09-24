class CsvLogger:
    """Writes rows to a CSV file using named columns instead of positional values."""

    def __init__(self, filename, columns):
        self.columns = columns
        self.file = open(filename, "w")
        self.file.write(",".join(columns) + "\r\n")
        self.file.flush()

    def log(self, **values):
        # missing columns are written as empty fields so rows stay aligned
        row = [str(values.get(col, "")) for col in self.columns]
        self.file.write(",".join(row) + "\r\n")
        self.file.flush()

    def close(self):
        self.file.close()
