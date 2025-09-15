-- Lending Platform Database Schema
-- Following the software-bug-assistant pattern for MCP Toolbox integration

CREATE TABLE loan_requests (
    id SERIAL PRIMARY KEY,
    borrower_address VARCHAR(255) NOT NULL,
    amount_algo DECIMAL(20, 6) NOT NULL,
    duration_days INTEGER NOT NULL,
    interest_rate DECIMAL(5, 4),
    status VARCHAR(50) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE lenders (
    id SERIAL PRIMARY KEY,
    lender_address VARCHAR(255) NOT NULL UNIQUE,
    available_amount DECIMAL(20, 6) NOT NULL DEFAULT 0,
    interest_rate DECIMAL(5, 4) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE loans (
    id SERIAL PRIMARY KEY,
    loan_request_id INTEGER REFERENCES loan_requests(id),
    lender_id INTEGER REFERENCES lenders(id),
    borrower_address VARCHAR(255) NOT NULL,
    lender_address VARCHAR(255) NOT NULL,
    amount_algo DECIMAL(20, 6) NOT NULL,
    interest_rate DECIMAL(5, 4) NOT NULL,
    duration_days INTEGER NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    due_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for better performance
CREATE INDEX idx_loan_requests_borrower ON loan_requests(borrower_address);
CREATE INDEX idx_loan_requests_status ON loan_requests(status);
CREATE INDEX idx_lenders_address ON lenders(lender_address);
CREATE INDEX idx_loans_borrower ON loans(borrower_address);
CREATE INDEX idx_loans_lender ON loans(lender_address);
CREATE INDEX idx_loans_status ON loans(status);