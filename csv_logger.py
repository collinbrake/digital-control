class CsvLogger:
    """Writes rows to a CSV file using named columns instead of positional values."""

    def __init__(self, filename, columns, flush_every=50):
        self.columns = columns
        self.file = open(filename, "w")
        self.file.write(",".join(columns) + "\r\n")
        self.flush_every = flush_every
        self._rows_since_flush = 0
        self.file.flush()

    def log(self, **values):
        # missing columns are written as empty fields so rows stay aligned
        row = [str(values.get(col, "")) for col in self.columns]
        self.file.write(",".join(row) + "\r\n")

        # flushing every row forces a flash sync that can take
        # milliseconds, so only flush every N rows instead
        self._rows_since_flush += 1
        if self._rows_since_flush >= self.flush_every:
            self.file.flush()
            self._rows_since_flush = 0

    def close(self):
        self.file.flush()
        self.file.close()
