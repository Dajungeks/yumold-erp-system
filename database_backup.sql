--
-- PostgreSQL database dump
--

-- Dumped from database version 16.9 (84ade85)
-- Dumped by pg_dump version 16.9

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: approval_history; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.approval_history (
    id integer NOT NULL,
    request_id character varying(50) NOT NULL,
    action character varying(50) NOT NULL,
    action_by character varying(50) NOT NULL,
    action_by_name character varying(100),
    action_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    notes text
);


ALTER TABLE public.approval_history OWNER TO neondb_owner;

--
-- Name: approval_history_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.approval_history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.approval_history_id_seq OWNER TO neondb_owner;

--
-- Name: approval_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.approval_history_id_seq OWNED BY public.approval_history.id;


--
-- Name: approval_requests; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.approval_requests (
    id integer NOT NULL,
    request_id character varying(50) NOT NULL,
    request_type character varying(50) NOT NULL,
    title character varying(200) NOT NULL,
    description text,
    requester_id character varying(50) NOT NULL,
    requester_name character varying(100),
    approver_id character varying(50),
    approver_name character varying(100),
    amount numeric(15,2),
    currency character varying(10) DEFAULT 'USD'::character varying,
    status character varying(20) DEFAULT 'pending'::character varying,
    priority character varying(20) DEFAULT 'normal'::character varying,
    requested_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    approved_date timestamp without time zone,
    rejected_date timestamp without time zone,
    approval_notes text,
    related_document_id character varying(50),
    created_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.approval_requests OWNER TO neondb_owner;

--
-- Name: approval_requests_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.approval_requests_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.approval_requests_id_seq OWNER TO neondb_owner;

--
-- Name: approval_requests_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.approval_requests_id_seq OWNED BY public.approval_requests.id;


--
-- Name: business_processs; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.business_processs (
    id integer NOT NULL,
    item_id character varying(50) NOT NULL,
    name character varying(200),
    status character varying(20) DEFAULT 'active'::character varying,
    created_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.business_processs OWNER TO neondb_owner;

--
-- Name: business_processs_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.business_processs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.business_processs_id_seq OWNER TO neondb_owner;

--
-- Name: business_processs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.business_processs_id_seq OWNED BY public.business_processs.id;


--
-- Name: cash_flows; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.cash_flows (
    id integer NOT NULL,
    item_id character varying(50) NOT NULL,
    name character varying(200),
    status character varying(20) DEFAULT 'active'::character varying,
    created_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.cash_flows OWNER TO neondb_owner;

--
-- Name: cash_flows_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.cash_flows_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.cash_flows_id_seq OWNER TO neondb_owner;

--
-- Name: cash_flows_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.cash_flows_id_seq OWNED BY public.cash_flows.id;


--
-- Name: cash_transactions; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.cash_transactions (
    id integer NOT NULL,
    item_id character varying(50) NOT NULL,
    name character varying(200),
    status character varying(20) DEFAULT 'active'::character varying,
    created_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.cash_transactions OWNER TO neondb_owner;

--
-- Name: cash_transactions_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.cash_transactions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.cash_transactions_id_seq OWNER TO neondb_owner;

--
-- Name: cash_transactions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.cash_transactions_id_seq OWNED BY public.cash_transactions.id;


--
-- Name: customers; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.customers (
    id integer NOT NULL,
    customer_id character varying(50) NOT NULL,
    company_name character varying(200) NOT NULL,
    contact_person character varying(100),
    email character varying(255),
    phone character varying(50),
    country character varying(100),
    city character varying(100),
    address text,
    business_type character varying(100),
    status character varying(20) DEFAULT 'active'::character varying,
    notes text,
    created_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.customers OWNER TO neondb_owner;

--
-- Name: customers_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.customers_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.customers_id_seq OWNER TO neondb_owner;

--
-- Name: customers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.customers_id_seq OWNED BY public.customers.id;


--
-- Name: employees; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.employees (
    id integer NOT NULL,
    employee_id character varying(50) NOT NULL,
    name character varying(100) NOT NULL,
    english_name character varying(100),
    email character varying(255),
    phone character varying(50),
    "position" character varying(100),
    department character varying(100),
    hire_date date,
    status character varying(20) DEFAULT 'active'::character varying,
    region character varying(100),
    password character varying(255),
    created_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    gender character varying(10) DEFAULT 'Male'::character varying,
    nationality character varying(50) DEFAULT 'Korea'::character varying,
    residence_country character varying(50) DEFAULT 'Korea'::character varying,
    city character varying(100),
    address text,
    birth_date date,
    salary integer DEFAULT 0,
    salary_currency character varying(10) DEFAULT 'KRW'::character varying,
    driver_license character varying(50) DEFAULT 'None'::character varying,
    notes text,
    work_status character varying(20) DEFAULT 'Active'::character varying,
    access_level character varying(20) DEFAULT 'user'::character varying
);


ALTER TABLE public.employees OWNER TO neondb_owner;

--
-- Name: employees_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.employees_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.employees_id_seq OWNER TO neondb_owner;

--
-- Name: employees_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.employees_id_seq OWNED BY public.employees.id;


--
-- Name: exchange_rates; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.exchange_rates (
    id integer NOT NULL,
    item_id character varying(50) NOT NULL,
    name character varying(200),
    status character varying(20) DEFAULT 'active'::character varying,
    created_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.exchange_rates OWNER TO neondb_owner;

--
-- Name: exchange_rates_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.exchange_rates_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.exchange_rates_id_seq OWNER TO neondb_owner;

--
-- Name: exchange_rates_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.exchange_rates_id_seq OWNED BY public.exchange_rates.id;


--
-- Name: expense_requests; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.expense_requests (
    id integer NOT NULL,
    item_id character varying(50) NOT NULL,
    name character varying(200),
    status character varying(20) DEFAULT 'active'::character varying,
    created_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.expense_requests OWNER TO neondb_owner;

--
-- Name: expense_requests_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.expense_requests_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.expense_requests_id_seq OWNER TO neondb_owner;

--
-- Name: expense_requests_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.expense_requests_id_seq OWNED BY public.expense_requests.id;


--
-- Name: finished_products; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.finished_products (
    id integer NOT NULL,
    item_id character varying(50) NOT NULL,
    name character varying(200),
    status character varying(20) DEFAULT 'active'::character varying,
    created_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.finished_products OWNER TO neondb_owner;

--
-- Name: finished_products_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.finished_products_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.finished_products_id_seq OWNER TO neondb_owner;

--
-- Name: finished_products_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.finished_products_id_seq OWNED BY public.finished_products.id;


--
-- Name: inventorys; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.inventorys (
    id integer NOT NULL,
    item_id character varying(50) NOT NULL,
    name character varying(200),
    status character varying(20) DEFAULT 'active'::character varying,
    created_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.inventorys OWNER TO neondb_owner;

--
-- Name: inventorys_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.inventorys_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.inventorys_id_seq OWNER TO neondb_owner;

--
-- Name: inventorys_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.inventorys_id_seq OWNED BY public.inventorys.id;


--
-- Name: invoices; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.invoices (
    id integer NOT NULL,
    item_id character varying(50) NOT NULL,
    name character varying(200),
    status character varying(20) DEFAULT 'active'::character varying,
    created_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.invoices OWNER TO neondb_owner;

--
-- Name: invoices_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.invoices_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.invoices_id_seq OWNER TO neondb_owner;

--
-- Name: invoices_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.invoices_id_seq OWNED BY public.invoices.id;


--
-- Name: master_products; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.master_products (
    id integer NOT NULL,
    product_code character varying(100) NOT NULL,
    product_name character varying(200) NOT NULL,
    category character varying(100),
    subcategory character varying(100),
    hrct_code character varying(50),
    hrcs_code character varying(50),
    specification text,
    unit character varying(20),
    weight numeric(10,3),
    dimensions character varying(100),
    material character varying(100),
    origin_country character varying(50),
    manufacturer character varying(200),
    model_number character varying(100),
    certification text,
    status character varying(20) DEFAULT 'active'::character varying,
    notes text,
    created_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.master_products OWNER TO neondb_owner;

--
-- Name: master_products_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.master_products_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.master_products_id_seq OWNER TO neondb_owner;

--
-- Name: master_products_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.master_products_id_seq OWNED BY public.master_products.id;


--
-- Name: monthly_saless; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.monthly_saless (
    id integer NOT NULL,
    item_id character varying(50) NOT NULL,
    name character varying(200),
    status character varying(20) DEFAULT 'active'::character varying,
    created_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.monthly_saless OWNER TO neondb_owner;

--
-- Name: monthly_saless_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.monthly_saless_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.monthly_saless_id_seq OWNER TO neondb_owner;

--
-- Name: monthly_saless_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.monthly_saless_id_seq OWNED BY public.monthly_saless.id;


--
-- Name: notes; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.notes (
    id integer NOT NULL,
    item_id character varying(50) NOT NULL,
    name character varying(200),
    status character varying(20) DEFAULT 'active'::character varying,
    created_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.notes OWNER TO neondb_owner;

--
-- Name: notes_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.notes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.notes_id_seq OWNER TO neondb_owner;

--
-- Name: notes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.notes_id_seq OWNED BY public.notes.id;


--
-- Name: notice_reads; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.notice_reads (
    id integer NOT NULL,
    read_id character varying(50) NOT NULL,
    notice_id character varying(50) NOT NULL,
    user_id character varying(50) NOT NULL,
    user_name character varying(100),
    read_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.notice_reads OWNER TO neondb_owner;

--
-- Name: notice_reads_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.notice_reads_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.notice_reads_id_seq OWNER TO neondb_owner;

--
-- Name: notice_reads_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.notice_reads_id_seq OWNED BY public.notice_reads.id;


--
-- Name: notices; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.notices (
    id integer NOT NULL,
    item_id character varying(50) NOT NULL,
    name character varying(200),
    status character varying(20) DEFAULT 'active'::character varying,
    created_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    notice_id character varying(50),
    title character varying(500) NOT NULL,
    content text NOT NULL,
    category character varying(50) DEFAULT 'general'::character varying,
    priority character varying(20) DEFAULT 'normal'::character varying,
    target_audience character varying(50) DEFAULT 'all'::character varying,
    department character varying(100),
    author_id character varying(50),
    author_name character varying(100),
    publish_date timestamp without time zone,
    expire_date timestamp without time zone,
    is_pinned integer DEFAULT 0,
    view_count integer DEFAULT 0,
    attachments text,
    tags text,
    title_en character varying(500),
    title_vi character varying(500),
    content_en text,
    content_vi text
);


ALTER TABLE public.notices OWNER TO neondb_owner;

--
-- Name: notices_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.notices_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.notices_id_seq OWNER TO neondb_owner;

--
-- Name: notices_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.notices_id_seq OWNED BY public.notices.id;


--
-- Name: order_items; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.order_items (
    id integer NOT NULL,
    order_id character varying(50) NOT NULL,
    item_number integer,
    product_name character varying(200),
    product_code character varying(100),
    specification text,
    quantity integer,
    unit_price numeric(15,2),
    total_price numeric(15,2),
    unit character varying(20),
    delivery_status character varying(20) DEFAULT 'pending'::character varying,
    notes text,
    created_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.order_items OWNER TO neondb_owner;

--
-- Name: order_items_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.order_items_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.order_items_id_seq OWNER TO neondb_owner;

--
-- Name: order_items_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.order_items_id_seq OWNED BY public.order_items.id;


--
-- Name: orders; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.orders (
    id integer NOT NULL,
    order_id character varying(50) NOT NULL,
    quotation_id character varying(50),
    customer_id character varying(50) NOT NULL,
    order_number character varying(100),
    order_date date,
    delivery_date date,
    currency character varying(10) DEFAULT 'USD'::character varying,
    exchange_rate numeric(10,4),
    total_amount numeric(15,2),
    status character varying(20) DEFAULT 'pending'::character varying,
    notes text,
    created_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    customer_company_name character varying(200),
    customer_contact_person character varying(100),
    customer_email character varying(255),
    customer_phone character varying(50),
    customer_address text,
    project_name character varying(200),
    payment_terms text,
    delivery_terms text,
    sales_rep_name character varying(100),
    sales_rep_email character varying(255)
);


ALTER TABLE public.orders OWNER TO neondb_owner;

--
-- Name: orders_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.orders_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.orders_id_seq OWNER TO neondb_owner;

--
-- Name: orders_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.orders_id_seq OWNED BY public.orders.id;


--
-- Name: product_codes; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.product_codes (
    id integer NOT NULL,
    item_id character varying(50) NOT NULL,
    name character varying(200),
    status character varying(20) DEFAULT 'active'::character varying,
    created_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.product_codes OWNER TO neondb_owner;

--
-- Name: product_codes_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.product_codes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.product_codes_id_seq OWNER TO neondb_owner;

--
-- Name: product_codes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.product_codes_id_seq OWNED BY public.product_codes.id;


--
-- Name: products; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.products (
    id integer NOT NULL,
    product_id character varying(50) NOT NULL,
    product_name character varying(200) NOT NULL,
    product_code character varying(100),
    category character varying(100),
    subcategory character varying(100),
    specification text,
    unit character varying(20),
    standard_price numeric(15,2),
    currency character varying(10) DEFAULT 'USD'::character varying,
    supplier_id character varying(50),
    lead_time character varying(100),
    status character varying(20) DEFAULT 'active'::character varying,
    notes text,
    created_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.products OWNER TO neondb_owner;

--
-- Name: products_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.products_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.products_id_seq OWNER TO neondb_owner;

--
-- Name: products_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.products_id_seq OWNED BY public.products.id;


--
-- Name: quotation_items; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.quotation_items (
    id integer NOT NULL,
    quotation_id character varying(50) NOT NULL,
    item_number integer,
    product_name character varying(200),
    product_code character varying(100),
    specification text,
    quantity integer,
    unit_price numeric(15,2),
    total_price numeric(15,2),
    unit character varying(20),
    lead_time character varying(100),
    notes text,
    created_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.quotation_items OWNER TO neondb_owner;

--
-- Name: quotation_items_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.quotation_items_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.quotation_items_id_seq OWNER TO neondb_owner;

--
-- Name: quotation_items_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.quotation_items_id_seq OWNED BY public.quotation_items.id;


--
-- Name: quotations; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.quotations (
    id integer NOT NULL,
    quotation_id character varying(50) NOT NULL,
    customer_id character varying(50) NOT NULL,
    quotation_number character varying(100),
    quotation_date date,
    delivery_date date,
    currency character varying(10) DEFAULT 'USD'::character varying,
    exchange_rate numeric(10,4),
    total_amount numeric(15,2),
    status character varying(20) DEFAULT 'draft'::character varying,
    notes text,
    created_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    revision_number integer DEFAULT 0,
    original_quotation_id character varying(50),
    project_name character varying(200),
    project_description text,
    payment_terms text,
    validity_period character varying(100),
    delivery_terms text,
    sales_rep_name character varying(100),
    sales_rep_email character varying(255),
    customer_company_name character varying(200),
    customer_contact_person character varying(100),
    customer_email character varying(255),
    customer_phone character varying(50),
    customer_address text
);


ALTER TABLE public.quotations OWNER TO neondb_owner;

--
-- Name: quotations_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.quotations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.quotations_id_seq OWNER TO neondb_owner;

--
-- Name: quotations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.quotations_id_seq OWNED BY public.quotations.id;


--
-- Name: sales_products; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.sales_products (
    id integer NOT NULL,
    item_id character varying(50) NOT NULL,
    name character varying(200),
    status character varying(20) DEFAULT 'active'::character varying,
    created_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.sales_products OWNER TO neondb_owner;

--
-- Name: sales_products_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.sales_products_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.sales_products_id_seq OWNER TO neondb_owner;

--
-- Name: sales_products_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.sales_products_id_seq OWNED BY public.sales_products.id;


--
-- Name: shippings; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.shippings (
    id integer NOT NULL,
    item_id character varying(50) NOT NULL,
    name character varying(200),
    status character varying(20) DEFAULT 'active'::character varying,
    created_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.shippings OWNER TO neondb_owner;

--
-- Name: shippings_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.shippings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.shippings_id_seq OWNER TO neondb_owner;

--
-- Name: shippings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.shippings_id_seq OWNED BY public.shippings.id;


--
-- Name: suppliers; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.suppliers (
    id integer NOT NULL,
    supplier_id character varying(50) NOT NULL,
    company_name character varying(200) NOT NULL,
    contact_person character varying(100),
    email character varying(100),
    phone character varying(50),
    address text,
    country character varying(50),
    city character varying(50),
    business_type character varying(100),
    payment_terms character varying(100),
    credit_limit numeric(15,2) DEFAULT 0,
    currency character varying(10) DEFAULT 'USD'::character varying,
    status character varying(20) DEFAULT 'active'::character varying,
    notes text,
    created_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.suppliers OWNER TO neondb_owner;

--
-- Name: suppliers_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.suppliers_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.suppliers_id_seq OWNER TO neondb_owner;

--
-- Name: suppliers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.suppliers_id_seq OWNED BY public.suppliers.id;


--
-- Name: system_config_history; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.system_config_history (
    id integer NOT NULL,
    history_id character varying(50) NOT NULL,
    config_key character varying(100) NOT NULL,
    old_value text,
    new_value text,
    change_reason text,
    changed_by character varying(100),
    changed_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.system_config_history OWNER TO neondb_owner;

--
-- Name: system_config_history_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.system_config_history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.system_config_history_id_seq OWNER TO neondb_owner;

--
-- Name: system_config_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.system_config_history_id_seq OWNED BY public.system_config_history.id;


--
-- Name: system_configs; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.system_configs (
    id integer NOT NULL,
    item_id character varying(50) NOT NULL,
    name character varying(200),
    status character varying(20) DEFAULT 'active'::character varying,
    created_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.system_configs OWNER TO neondb_owner;

--
-- Name: system_configs_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.system_configs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.system_configs_id_seq OWNER TO neondb_owner;

--
-- Name: system_configs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.system_configs_id_seq OWNED BY public.system_configs.id;


--
-- Name: user_notes; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.user_notes (
    note_id character varying(100) NOT NULL,
    user_id character varying(50) NOT NULL,
    page_name character varying(100) NOT NULL,
    note_content text NOT NULL,
    created_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.user_notes OWNER TO neondb_owner;

--
-- Name: user_sessions; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.user_sessions (
    id integer NOT NULL,
    session_id character varying(100) NOT NULL,
    user_id character varying(50) NOT NULL,
    created_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    expires_date timestamp without time zone,
    is_active boolean DEFAULT true
);


ALTER TABLE public.user_sessions OWNER TO neondb_owner;

--
-- Name: user_sessions_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.user_sessions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.user_sessions_id_seq OWNER TO neondb_owner;

--
-- Name: user_sessions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.user_sessions_id_seq OWNED BY public.user_sessions.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.users (
    id integer NOT NULL,
    user_id character varying(50) NOT NULL,
    username character varying(100) NOT NULL,
    email character varying(100),
    password_hash character varying(255) NOT NULL,
    access_level character varying(20) DEFAULT 'user'::character varying,
    is_active boolean DEFAULT true,
    last_login timestamp without time zone,
    created_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.users OWNER TO neondb_owner;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO neondb_owner;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: vacations; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.vacations (
    id integer NOT NULL,
    item_id character varying(50) NOT NULL,
    name character varying(200),
    status character varying(20) DEFAULT 'active'::character varying,
    created_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.vacations OWNER TO neondb_owner;

--
-- Name: vacations_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.vacations_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.vacations_id_seq OWNER TO neondb_owner;

--
-- Name: vacations_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.vacations_id_seq OWNED BY public.vacations.id;


--
-- Name: weekly_reports; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.weekly_reports (
    id integer NOT NULL,
    item_id character varying(50) NOT NULL,
    name character varying(200),
    status character varying(20) DEFAULT 'active'::character varying,
    created_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.weekly_reports OWNER TO neondb_owner;

--
-- Name: weekly_reports_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.weekly_reports_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.weekly_reports_id_seq OWNER TO neondb_owner;

--
-- Name: weekly_reports_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.weekly_reports_id_seq OWNED BY public.weekly_reports.id;


--
-- Name: work_statuss; Type: TABLE; Schema: public; Owner: neondb_owner
--

CREATE TABLE public.work_statuss (
    id integer NOT NULL,
    item_id character varying(50) NOT NULL,
    name character varying(200),
    status character varying(20) DEFAULT 'active'::character varying,
    created_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_date timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.work_statuss OWNER TO neondb_owner;

--
-- Name: work_statuss_id_seq; Type: SEQUENCE; Schema: public; Owner: neondb_owner
--

CREATE SEQUENCE public.work_statuss_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.work_statuss_id_seq OWNER TO neondb_owner;

--
-- Name: work_statuss_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: neondb_owner
--

ALTER SEQUENCE public.work_statuss_id_seq OWNED BY public.work_statuss.id;


--
-- Name: approval_history id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.approval_history ALTER COLUMN id SET DEFAULT nextval('public.approval_history_id_seq'::regclass);


--
-- Name: approval_requests id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.approval_requests ALTER COLUMN id SET DEFAULT nextval('public.approval_requests_id_seq'::regclass);


--
-- Name: business_processs id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.business_processs ALTER COLUMN id SET DEFAULT nextval('public.business_processs_id_seq'::regclass);


--
-- Name: cash_flows id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.cash_flows ALTER COLUMN id SET DEFAULT nextval('public.cash_flows_id_seq'::regclass);


--
-- Name: cash_transactions id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.cash_transactions ALTER COLUMN id SET DEFAULT nextval('public.cash_transactions_id_seq'::regclass);


--
-- Name: customers id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.customers ALTER COLUMN id SET DEFAULT nextval('public.customers_id_seq'::regclass);


--
-- Name: employees id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.employees ALTER COLUMN id SET DEFAULT nextval('public.employees_id_seq'::regclass);


--
-- Name: exchange_rates id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.exchange_rates ALTER COLUMN id SET DEFAULT nextval('public.exchange_rates_id_seq'::regclass);


--
-- Name: expense_requests id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.expense_requests ALTER COLUMN id SET DEFAULT nextval('public.expense_requests_id_seq'::regclass);


--
-- Name: finished_products id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.finished_products ALTER COLUMN id SET DEFAULT nextval('public.finished_products_id_seq'::regclass);


--
-- Name: inventorys id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.inventorys ALTER COLUMN id SET DEFAULT nextval('public.inventorys_id_seq'::regclass);


--
-- Name: invoices id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.invoices ALTER COLUMN id SET DEFAULT nextval('public.invoices_id_seq'::regclass);


--
-- Name: master_products id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.master_products ALTER COLUMN id SET DEFAULT nextval('public.master_products_id_seq'::regclass);


--
-- Name: monthly_saless id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.monthly_saless ALTER COLUMN id SET DEFAULT nextval('public.monthly_saless_id_seq'::regclass);


--
-- Name: notes id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.notes ALTER COLUMN id SET DEFAULT nextval('public.notes_id_seq'::regclass);


--
-- Name: notice_reads id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.notice_reads ALTER COLUMN id SET DEFAULT nextval('public.notice_reads_id_seq'::regclass);


--
-- Name: notices id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.notices ALTER COLUMN id SET DEFAULT nextval('public.notices_id_seq'::regclass);


--
-- Name: order_items id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.order_items ALTER COLUMN id SET DEFAULT nextval('public.order_items_id_seq'::regclass);


--
-- Name: orders id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.orders ALTER COLUMN id SET DEFAULT nextval('public.orders_id_seq'::regclass);


--
-- Name: product_codes id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.product_codes ALTER COLUMN id SET DEFAULT nextval('public.product_codes_id_seq'::regclass);


--
-- Name: products id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.products ALTER COLUMN id SET DEFAULT nextval('public.products_id_seq'::regclass);


--
-- Name: quotation_items id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.quotation_items ALTER COLUMN id SET DEFAULT nextval('public.quotation_items_id_seq'::regclass);


--
-- Name: quotations id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.quotations ALTER COLUMN id SET DEFAULT nextval('public.quotations_id_seq'::regclass);


--
-- Name: sales_products id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.sales_products ALTER COLUMN id SET DEFAULT nextval('public.sales_products_id_seq'::regclass);


--
-- Name: shippings id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.shippings ALTER COLUMN id SET DEFAULT nextval('public.shippings_id_seq'::regclass);


--
-- Name: suppliers id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.suppliers ALTER COLUMN id SET DEFAULT nextval('public.suppliers_id_seq'::regclass);


--
-- Name: system_config_history id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.system_config_history ALTER COLUMN id SET DEFAULT nextval('public.system_config_history_id_seq'::regclass);


--
-- Name: system_configs id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.system_configs ALTER COLUMN id SET DEFAULT nextval('public.system_configs_id_seq'::regclass);


--
-- Name: user_sessions id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.user_sessions ALTER COLUMN id SET DEFAULT nextval('public.user_sessions_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Name: vacations id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.vacations ALTER COLUMN id SET DEFAULT nextval('public.vacations_id_seq'::regclass);


--
-- Name: weekly_reports id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.weekly_reports ALTER COLUMN id SET DEFAULT nextval('public.weekly_reports_id_seq'::regclass);


--
-- Name: work_statuss id; Type: DEFAULT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.work_statuss ALTER COLUMN id SET DEFAULT nextval('public.work_statuss_id_seq'::regclass);


--
-- Data for Name: approval_history; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.approval_history (id, request_id, action, action_by, action_by_name, action_date, notes) FROM stdin;
\.


--
-- Data for Name: approval_requests; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.approval_requests (id, request_id, request_type, title, description, requester_id, requester_name, approver_id, approver_name, amount, currency, status, priority, requested_date, approved_date, rejected_date, approval_notes, related_document_id, created_date, updated_date) FROM stdin;
\.


--
-- Data for Name: business_processs; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.business_processs (id, item_id, name, status, created_date, updated_date) FROM stdin;
\.


--
-- Data for Name: cash_flows; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.cash_flows (id, item_id, name, status, created_date, updated_date) FROM stdin;
\.


--
-- Data for Name: cash_transactions; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.cash_transactions (id, item_id, name, status, created_date, updated_date) FROM stdin;
\.


--
-- Data for Name: customers; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.customers (id, customer_id, company_name, contact_person, email, phone, country, city, address, business_type, status, notes, created_date, updated_date) FROM stdin;
3	C001	VIET NAM HTMP MECHANICAL COMPANY LIMITED	Mr. Manh	vuong_dinh_manh@htmp.com.vn	091-3317616	Vietnam	NaN	No. 27, D1, Dai Kim New Urban Area, Hoang Mai, Hanoi	NaN	활성	NaN	2025-09-08 10:31:50	2025-09-08 10:31:50
4	C002	VIET NAM HTMP JOINT STOCK COMPANY	Mr. Hao	nguyen_van_hao@htmp.com.vn	091-3257359	Vietnam	NaN	Lot 43 D3, Quang Minh Industrial Park, Chi Dong Town, Me Linh District, Hanoi	NaN	활성	NaN	2025-09-08 10:31:51	2025-09-08 10:31:51
5	C003	HTMP VIETNAM COMPANY	Mr. Phuong	hoang_viet_phuong@htmp.com.vn	091-4689000	Vietnam	NaN	Lot CN1-02B-1&2, No#1 Hi-Tech Industrial Park, Hoa Lac Hi-Tech Park, Km29 Thang Long Avenue, Ha Noi City, Vietnam	NaN	활성	NaN	2025-09-08 10:31:52	2025-09-08 10:31:52
6	C004	TOHO VIETNAM COMPANY LIMITED	Mr. Dong	pc4@toho.com.vn	097-4211789	Japan	NaN	Lot B1, Thang Long IP, Kim Chung Commune, Dong Anh District, Hanoi City, Vietnam	NaN	활성	NaN	2025-09-08 10:31:56	2025-09-08 10:31:56
7	C005	VIETNAM TMT MOLD AND INDUSTRY EQUIPMENT JOINT STOCK COMPANY 	Ms. Hanh	sales-02@tmt-mold.com.vn	032-92077668	Vietnam	NaN	No. 8 Trang Tien - Trang Tien Ward - Hoan Kiem District	NaN	활성	NaN	2025-09-08 10:31:57	2025-09-08 10:31:57
8	C006	BRANCH OF PANASONIC SYSTEM NETWORKS VIETNAM CO.,LTD IN HANOI	Ms. Huyen	thihuyen.kieu@vn.panasonic.com	096-7212208	Japan	NaN	Lot J1/2, Thang Long Industrial Park, Vong La Commune, Dong Anh District, Hanoi	NaN	활성	NaN	2025-09-08 10:31:58	2025-09-08 10:31:58
9	C007	PANASONIC APPLIANCES VIETNAM CO., LTD.	Mr. Thai	thai.dokhac@vn.panasonic.com	0329-000123	Japan	NaN	Plot B-6, Thang Long I IP – Dong Anh – Ha Noi	NaN	활성	NaN	2025-09-08 10:31:59	2025-09-08 10:31:59
10	C008	HANOI PLASTICS JOINT STOCK COMPANY	Mr. Quan	quan.kttk@hpcvn.vn	091-2598968	Vietnam	NaN	Group 12, Phuc Loi Ward, Long Bien District, Hanoi	NaN	활성	NaN	2025-09-08 10:32:00	2025-09-08 10:32:00
11	C009	MUTO TECHNOLOGY HA NOI CO.,LTD	Ms. Loan	muahang@mutohanoi.com.vn	098-9255904	Japan	NaN	Lot 37, Quang Minh Industrial Park - Quang Minh Town - Me Linh District - Hanoi.	NaN	활성	NaN	2025-09-08 10:32:02	2025-09-08 10:32:02
12	C010	ROKI VIETNAM CO., LTD	Mr. Thien	thien_dd@roki-vn.com	097-8776596	Vietnam	NaN	Lot 72 - 73, Noi Bai Industrial Park - Quang Tien Commune - Soc Son District - Hanoi.	NaN	활성	NaN	2025-09-08 10:32:03	2025-09-08 10:32:03
13	C011	HANEL PLASTICS JOINT STOCK COMPANY	Mr. Phong	phong.dothu@gmail.com	090-4106147	Vietnam	NaN	B15, Industrial Road No. 6, Sai Dong B Industrial Park, Sai Dong Ward, Long Bien District, Hanoi	NaN	활성	NaN	2025-09-08 10:32:04	2025-09-08 10:32:04
14	C012	LIHAI METAL ENGINEERING COMPANY LIMITED	Ms. Thuan	sale01@lihaisteel.com	098-4189689	China	NaN	Lot 38E Quang Minh Industrial Park, Me Linh Center, Hanoi 	NaN	활성	NaN	2025-09-08 10:32:05	2025-09-08 10:32:05
15	C013	VIET NAM PRODUCTION MOLD JOINT STOCK COMPANY	Mr. Quynh	salevnmold@gmail.com	098-6699386	Vietnam	NaN	Lai Xa Industrial Park, Kim Chung, Hoai Duc, Hanoi, Vietnam	NaN	활성	NaN	2025-09-08 10:32:06	2025-09-08 10:32:06
16	C014	HANOI MOLD TECHNOLOGY COMPANY LIMITED	Mr. Hung	khuonmauvt@gmail.com	091-2308979	Vietnam	NaN	Cao Xa Village, Duc Thuong Commune, Hoai Duc District, Hanoi, Vietnam 	NaN	활성	NaN	2025-09-08 10:32:07	2025-09-08 10:32:07
17	C015	VIET CHUAN JOINT STOCK COMPANY	Ms. Huong	pur1@vietchuan.vn	034-9602270	Vietnam	NaN	Lot B2-3-1b Nam Thang Long IP, Tan Phong Street, Thuy Phuong Ward, Bac Tu Liem District, Hanoi	NaN	활성	NaN	2025-09-08 10:32:09	2025-09-08 10:32:09
18	C016	AVIATION PREMIUM PLASTICS JOINT STOCK COMPANY (APLACO)	Mr. Tuan	tuankt@gmail.com	091-5076500	Vietnam	NaN	Lane 200, Nguyen Son Street, Bo De Ward, Long Bien District, Hanoi	NaN	활성	NaN	2025-09-08 10:32:10	2025-09-08 10:32:10
19	C017	ALPHA VIETNAM COMPANY LIMITED	Ms. Lien	marketing@alphavietnam.com.vn	035-7828788	Vietnam	NaN	Lot K-2, Thang Long Industrial Park, Vong La Commune, Dong Anh District, Hanoi City, Vietnam.	NaN	활성	NaN	2025-09-08 10:32:11	2025-09-08 10:32:11
20	C018	VIETNAM STANLEY ELECTRIC CO., LTD	Ms. Loan	loannt@stanley.com.vn	098-8684546	Japan	NaN	Duong Xa, Gia Lam, Hanoi - Duong Xa Commune - Gia Lam District - Hanoi.	NaN	활성	NaN	2025-09-08 10:32:12	2025-09-08 10:32:12
21	C019	DAIWA VIETNAM LIMITED	Mr. Anh	anh-pd@daiwa-tl.com	098-8823524	Vietnam	NaN	Lot K8, Thang Long Industrial Park, Vong La Commune, Dong Anh District, Hanoi City, Vietnam	NaN	활성	NaN	2025-09-08 10:32:13	2025-09-08 10:32:13
22	C020	FLEDO COMPANY LIMITED	Ms. Hang	t-hang@fledo.com.vn	096-3962669	Vietnam	NaN	No. 22A1, Group 6, Nguyen Van Linh Street, Phuc Dong Ward, Long Bien District, Hanoi City, Vietnam	NaN	활성	NaN	2025-09-08 10:32:14	2025-09-08 10:32:14
23	C021	HIKARI VIETNAM PRODUCTION AND TRADING COMPANY LIMITED.	Mr. Tuan	stock@hikarivn.com	094-5806655	Vietnam	NaN	Road 70, Nhue Giang Residential Group, Tay Mo Ward, Nam Tu Liem District, Hanoi City, Vietnam	NaN	활성	NaN	2025-09-08 10:32:16	2025-09-08 10:32:16
24	C022	MINKOREA TRAINING SERVICES AND INTERNATIONAL COOPERATION COMPANY LIMITED	Mr. Son	sonpham216@gmail.com	037-4480174	Vietnam	NaN	Trade Floor OF-06, Building R4 - No. 72A Nguyen Trai, Thuong Dinh Ward, Thanh Xuan District, Hanoi City, Vietnam	NaN	활성	NaN	2025-09-08 10:32:17	2025-09-08 10:32:17
25	C023	ELENTEC VIETNAM COMPANY LIMITED	Ms. Thai	thaivth@elentec.vn	097-3617311	Korea	NaN	Lot 44F, 44J, Quang Minh Industrial Park - Chi Dong Town - Me Linh District - Hanoi.	NaN	활성	NaN	2025-09-08 10:32:18	2025-09-08 10:32:18
26	C024	APS COMPANY LIMITED	Mr Tuyen	trungtuyen@gmail.com	098-9441989	Vietnam	NaN	Residential Group No. 9, Quang Minh Town, Me Linh District, Hanoi City, Vietnam	NaN	활성	NaN	2025-09-08 10:32:19	2025-09-08 10:32:19
27	C025	BM SYSTEM SOLUTION COMPANY LIMITED	Ms. Yen	bmssvina@daum.net	096-9687655	Vietnam	NaN	T1, C21, Lot BT105, Bac An Khanh New Urban Area, Splendora, An Khanh Commune, Hoai Duc District, Hanoi	NaN	활성	NaN	2025-09-08 10:32:20	2025-09-08 10:32:20
28	C026	CAD PLASTIC COMPANY LIMITED	Ms. Thuy	ngo_thi_thuy@cadplastic.com.vn	0983-103658	Vietnam	NaN	Lot 49G, Quang Minh Industrial Park, TT. Quang Minh, H. Me Linh, Hanoi	NaN	활성	NaN	2025-09-08 10:32:22	2025-09-08 10:32:22
29	C027	ELENTEC VIETNAM ENERGY COMPANY LIMITED	Ms. Van	thanhvan@elentec.vn	098-4623455	Korea	NaN	Lot 44D, Quang Minh Industrial Park, Chi Dong Town, Me Linh District, Hanoi City, Vietnam	NaN	활성	NaN	2025-09-08 10:32:23	2025-09-08 10:32:23
30	C028	FAGETECH PRODUCE COMMERCIAL SERVICE COMPANY LIMITED	Mr Ho	fagetech.company@gmail.com	096-1626359	Vietnam	NaN	14th floor, Zen Tower Building, 12 Khuat Duy Tien Street, Thanh Xuan Trung Ward, Thanh Xuan District, Hanoi City, Vietnam	NaN	활성	NaN	2025-09-08 10:32:24	2025-09-08 10:32:24
31	C029	LG ELECTRONICS VIETNAM HAI PHONG CO., LTD	Mr Hoang	hoang.do@lge.com	NaN	Korea	NaN	Lot E Trang Due industrial park, belonging to Dinh Vu - Cat Hai economic zone, Hong Phong Commune, An Duong District, Hai Phong City, Vietnam	NaN	활성	NaN	2025-09-08 10:32:25	2025-09-08 10:32:25
32	C030	INMAS VIET NAM COMPANY LIMITED	Mr. Huy	huy.electronic@gmail.com	0362-882886	Vietnam	NaN	No. 14, Trung Yen 3 Street, Trung Hoa Ward, Cau Giay District, Hanoi	NaN	활성	NaN	2025-09-08 10:32:26	2025-09-08 10:32:26
33	C031	MOLDPIA COMPANY LIMITED	Mr. Trí	moldpiavietnam@gmail.com	096-1201608	Korea	NaN	Lot No. 29A, Me Linh Industrial Park, TT. Quang Minh, H. Me Linh, Hanoi	NaN	활성	NaN	2025-09-08 10:32:27	2025-09-08 10:32:27
34	C032	VIET NAM OSAKA JOINT STOCK COMPANY	Mr. Thai	ngocthai@osakaseimitsu.vn	097-6888048	Vietnam	NaN	No. 66 Hoang Sam Street, Nghia Do Ward, Cau Giay District, Hanoi	NaN	활성	NaN	2025-09-08 10:32:29	2025-09-08 10:32:29
35	C033	SHIMIZU CORPORATION	Mr. Trung	pttrung@shimizu-iv.com	0901 – 448 – 775	Vietnam	NaN	7th Floor, VTP Building No. 8, Nguyen Hue Street, Ben Nghe Ward, District 1, Ho Chi Minh City, Vietnam	NaN	활성	NaN	2025-09-08 10:32:30	2025-09-08 10:32:30
36	C034	SHINMEIDO INDUSTRIAL JOINT STOCK COMPANY	Mr. Thai	trongthai@shinmeido.com.vn	090-3211715	Vietnam	NaN	Zone II, Phu Minh Commune, Soc Son District, Hanoi City	NaN	활성	NaN	2025-09-08 10:32:31	2025-09-08 10:32:31
37	C035	SUNHOUSE GROUP JOINT STOCK COMPANY	NaN	info@sunhouse.com.vn.	NaN	Vietnam	NaN	No. 139, Nguyen Thai Hoc Street, Dien Bien Ward, Ba Dinh District, Hanoi City, Vietnam	NaN	활성	NaN	2025-09-08 10:32:32	2025-09-08 10:32:32
38	C036	TAN PHAT ETEK TECHNOLOGY SERVICES JOINT STOCK COMPANY	Mr Lam	lamnq.tbcn@tanphat.com	086-9163869	Vietnam	NaN	No. 189 Phan Trong Tue, Thanh Liet Commune, Thanh Tri District, Hanoi	NaN	활성	NaN	2025-09-08 10:32:33	2025-09-08 10:32:33
39	C037	TENMA (HCM) VIETNAM CO., LTD. HANOI BRANCH	Mr. Cuong	tiennv@tenmacorp.co.jp	091-4825217	Japan	NaN	Lot 88 (Area A), Noi Bai Industrial Park, Quang Tien Commune, Soc Son District, Hanoi	NaN	활성	NaN	2025-09-08 10:32:34	2025-09-08 10:32:34
40	C038	VINSMART RESEARCH AND MANUFACTURE JOINT STOCK COMPANY	Mr. Kien	v.KienDN3@vinsmart.vn	098-1612643	Vietnam	NaN	Lot CN1-06B-1&2 Hi-tech Industrial Park 1, Hoa Lac Hi-Tech Park, Ha Bang Commune, Thach That District, Hanoi City, Vietnam	NaN	활성	NaN	2025-09-08 10:32:36	2025-09-08 10:32:36
41	C039	HYOSUNG FINANCIAL SYSTEM VINA	NaN	NaN	NaN	Korea	NaN	Lot CN8-1, Yen Phong II-C Industrial Park, Tam Giang Commune, Cho Town, Yen Phong District, Bac Ninh Province, Vietnam	NaN	활성	NaN	2025-09-08 10:32:37	2025-09-08 10:32:37
42	C040	VIETNAM PRECISION MECHANICAL, SERVICE AND TRADING COMPANY LIMITED	Ms. Huong	duonglanhuong11290@gmail.com	039-5171958	Vietnam	NaN	Lot C6 Dong Tho multi-professional industrial cluster, Dong Tho commune, Yen Phong district, Bac Ninh province, Vietnam	NaN	활성	NaN	2025-09-08 10:32:38	2025-09-08 10:32:38
43	C041	WOOJEON VINA COMPANY LIMITED	Ms. Thao	ntt-thao@woojeon.com.vn	097-3128496	Korea	NaN	Lot F2, Que Vo Industrial Park (expansion area), Phuong Lieu Commune, Que Vo District, Bac Ninh Province, Vietnam	NaN	활성	NaN	2025-09-08 10:32:39	2025-09-08 10:32:39
44	C042	SRITHAI (HANOI) COMPANY LIMITED	Ms. Thanh	thanhnt.shn@srithaivn.com.vn	094-7573238	Other	NaN	01, Road 3, VSIP Bac Ninh Service and Urban Industrial Park, Tu Son Town, Bac Ninh	NaN	활성	NaN	2025-09-08 10:32:40	2025-09-08 10:32:40
45	C043	SEJONG WISE VINA COMPANY LIMITED	Mr. Tan	sejong eng vina <seajong0617@gmail.com>	097-6269694	Korea	NaN	Lot D, Que Vo Industrial Park, Van Duong Ward, Bac Ninh City, Bac Ninh Province, Vietnam 	NaN	활성	NaN	2025-09-08 10:32:41	2025-09-08 10:32:41
48	C044	YOON IL VIETNAM COMPANY LIMITED	Mr. Kieu	giahankr335@gmail.com\nyoonilvina2013@gmail.com	098-7984390	Korea		Lot C8-2, Que Vo Industrial Park, Nam Son Commune, Bac Ninh City, Bac Ninh		active		2025-09-08 10:34:08	2025-09-08 10:34:08
49	C045	VIETNAM ZHONGYU PRECISE INDUSTRIAL COMPANY LIMITED	Ms. Thu	yuenancaigou@zhongyu.com.vn	096-8865516	China		Lot G6-1, Que Vo Industrial Park (expansion area), Phuong Lieu Commune, Que Vo District, Bac Ninh Province, Vietnam		active		2025-09-08 10:34:09	2025-09-08 10:34:09
50	C046	HUAXU VIET NAM MOLD COMPANY LIMITED	Mr. Huang	txy_huaxu@126.com	096-2464435	China		Ha Lieu Village, Phuong Lieu Commune, Que Vo District, Bac Ninh Province, Vietnam		active		2025-09-08 10:34:10	2025-09-08 10:34:10
51	C047	KDA M&C COMPANY LIMITED	Ms. Quynh	quynh.nguyenthi@kdagroup.co.kr	097-6471996	Vietnam		Yen Phong Industrial Park, Dong Phong Commune, Yen Phong District, Bac Ninh Province, Vietnam		active		2025-09-08 10:34:12	2025-09-08 10:34:12
52	C048	ZION JOINT STOCK COMPANY	Mr. Thien	nguyen xuan thien <thien.nx@zionplastic.vn>	098-3600689	Vietnam		No. 12, Street 10, VSIP Bac Ninh Industrial, Urban and Service Park, Dai Dong Commune, Tien Du District, Bac Ninh Province, Vietnam		active		2025-09-08 10:34:13	2025-09-08 10:34:13
53	C049	KAI VIETNAM CO., LTD	nan			Japan		Lot I-1&2, Thang Long Industrial Park, Vong La Commune, Dong Anh District, Hanoi City, Vietnam		active		2025-09-08 10:34:14	2025-09-08 10:34:14
54	C050	LEADERS ENG VINA COMPANY LIMITED	Ms. Thuy	duyanhthaoquyen88@gmail.com	098-3283388	Korea		Lot CNSG-07, Van Trung Industrial Park, Van Trung Commune, Viet Yen District, Bac Giang Province, Vietnam		active		2025-09-08 10:34:15	2025-09-08 10:34:15
55	C051	SEIYO VIETNAM COMPANY LIMITED	Ms. Ha	Pur1_svn@seiyo.com.vm	097-5730397	China		Lot D1, Que Vo Industrial Park, Nam Son Ward, Bac Ninh City, Bac Ninh Province, Vietnam		active		2025-09-08 10:34:16	2025-09-08 10:34:16
56	C052	PIN SHINE ELECTRONICS VIETNAM COMPANY LIMITED	Mr. Tang	shihsin@vn.pinshine.com	037-5764105	China		Lot CN2-6, Que Vo Industrial Park III, Viet Hung Commune, Que Vo District, Bac Ninh		active		2025-09-08 10:34:17	2025-09-08 10:34:17
57	C053	CNCTECH BAC NINH JOINT STOCK COMPANY	Ms. Ket	ket.duong@framashanoi.com	097-3092539	Vietnam		Lot H3-2, Dai Dong - Hoan Son Industrial Park, Tri Phuong Commune, Tien Du District, Bac Ninh Province, Vietnam		active		2025-09-08 10:34:19	2025-09-08 10:34:19
58	C054	FINE MS VINA COMPANY LIMITED.	Ms. Tuoi	letssmile18@gmail.com	035-6486608	Vietnam		Lot G2, Que Vo IZ, Nam Son ward, Bac Ninh city, Bac Ninh province, Vietnam		active		2025-09-08 10:34:20	2025-09-08 10:34:20
59	C055	MOTUS VINA COMPANY LIMITED	Mr. Dao	doandaobn@gmail.com	039-7138982	Vietnam		Factory No. 10-Lot A1 Dai Dong - Hoan Son Industrial Park, Hoan Son Commune, Tien Du District, Bac Ninh Province, Vietnam		active		2025-09-08 10:34:21	2025-09-08 10:34:21
60	C056	HANLIM COMPANY LIMITED	Ms. Khuyen	phamlekhuyen@gmail.com	036-2508660	Korea		Khac Niem Industrial Cluster, Khac Niem Ward, Bac Ninh City, Bac Ninh Province, Vietnam		active		2025-09-08 10:34:22	2025-09-08 10:34:22
61	C057	SEOJIN AUTO COMPANY LIMITED	Mr. Huong	nguyenhuongkh1315@gmail.com	093-6854583	Korea		TS3 Road, Tien Son Industrial Park (Tel: Viglacera Company) - Hoan Son Commune - Tien Du District - Bac Ninh.		active		2025-09-08 10:34:23	2025-09-08 10:34:23
62	C058	HANOI SEOWONINTECH COMPANY LIMITED	Mr. Trung	trunginjection@gmail.com	097-3764810	Vietnam		Yen Phong Industrial Park - Long Chau Commune - Yen Phong District - Bac Ninh.		active		2025-09-08 10:34:24	2025-09-08 10:34:24
63	C059	UIL VIETNAM JOINT STOCK COMPANY	Ms. Nhung	lenhung <lenhung@uil.com.vn>;	096-7869936	Vietnam		Lot F1, Que Vo Industrial Park (expansion area), Phuong Lieu Commune, Que Vo District, Bac Ninh Province, Vietnam		active		2025-09-08 10:34:26	2025-09-08 10:34:26
64	C060	VINA YONG SEONG COMPANY LIMITED	Ms. Thuan	thuthuantran90@gmail.com	038-9961445	Vietnam		Lot J6 Dai Dong - Hoan Son Industrial Park, Tan Hong Ward, Tu Son Town, Bac Ninh Province, Vietnam		active		2025-09-08 10:34:27	2025-09-08 10:34:27
65	C061	MOCA MOLD CO., LTD	nan			Korea		730-4, Gojan-dong, Namdong-gu,, Incheon		active		2025-09-08 10:34:28	2025-09-08 10:34:28
66	C062	BAC VIET JOINT STOCK COMPANY	Mr. Ha	admin@bacvietsteel.com	0399-092126	Vietnam		Km 7, National Highway 18, Phuong Lieu Commune, Que Vo District, Bac Ninh		active		2025-09-08 10:34:29	2025-09-08 10:34:29
67	C063	DAE SANG TECH VINA CO.,LTD	Mr. Trang	nguyenthitrangcnbn@gmail.com;	0355-867503	Korea		Lot G14, G1C road, Que Vo industrial park (expansion area), Phuong Lieu commune, Que Vo district, Bac Ninh province, Vietnam		active		2025-09-08 10:34:30	2025-09-08 10:34:30
68	C064	DS TECH VINA COMPANY LIMITED	Mr. Mai	thanhmaibui69@gmail.com;	0355-867503	Korea		Lot G14, G1C road, Que Vo industrial park (expansion area), Phuong Lieu commune, Que Vo district, Bac Ninh province, Vietnam		active		2025-09-08 10:34:31	2025-09-08 10:34:31
69	C065	ECOTEK COMPANY LIMITED	Mr. Hai	hai-bui@eco-tek.vn	098-2192286	Vietnam		Lot III.4.1 Thuan Thanh 3 Industrial Park, Thanh Khuong Commune, Thuan Thanh District, Bac Ninh Province, Vietnam		active		2025-09-08 10:34:33	2025-09-08 10:34:33
70	C066	ELENSYS VIETNAM COMPANY LIMITED	Mr. Viet	khacviet1986@gmail.com	097-5561986	Korea		TS9 Road, Tien Son Industrial Park, Tuong Giang Ward, Tu Son Town, Bac Ninh		active		2025-09-08 10:34:34	2025-09-08 10:34:34
71	C067	FOSTER ELECTRIC (VIETNAM) CO., LTD	Mr. Quang	vnmq@foster.com.vn	097-7555502	Japan		1, Street 11, Vsip Bac Ninh Urban and Service Industrial Park, Phu Chan Ward, Tu Son City, Bac Ninh Province, Vietnam		active		2025-09-08 10:34:35	2025-09-08 10:34:35
72	C068	GEO NATION VIETNAM COMPANY LIMITED	Mr Quan	trongquan@gmail.com	097-3475443	Korea		Lot CN07-7 Yen Phong Industrial Park Extension, Yen Trung Commune, Yen Phong District, Bac Ninh Province, Vietnam		active		2025-09-08 10:34:36	2025-09-08 10:34:36
73	C069	HANPO VINA JOINT STOCK COMPANY	Mr Canh	hanpo@hanpovina.vn	039-9173718	Vietnam		Lot CN07-6 Yen Phong Industrial Park Extension, Yen Trung Commune, Yen Phong District, Bac Ninh Province, Vietnam		active		2025-09-08 10:34:37	2025-09-08 10:34:37
74	C070	HZM HIGH DURABILITY PLASTIC MOULD MANUFACTURE JOINT VENTURE COMPANY LIMITED	Mr. Minh	xuanminh.mh@hzm.vn	098-3564176	Vietnam		Duc Hiep Hamlet, Xuan Lam Commune, Thuan Thanh District, Bac Ninh Province, Vietnam		active		2025-09-08 10:34:38	2025-09-08 10:34:38
75	C071	INTOPS VIETNAM COMPANY LIMITED	Mr. Tan	nguyenthisau189@gmail.com	097-6777592	Korea		Yen Phong Industrial Park, Long Chau Commune, Yen Phong District, Bac Ninh Province		active		2025-09-08 10:34:40	2025-09-08 10:34:40
76	C072	KISHIN VIETNAM COMPANY LIMITED	Mr. Lam	lam.tai@kishin.com	094-6088683	Korea		Que Vo Industrial Park, Nam Son, Bac Ninh City		active		2025-09-08 10:34:41	2025-09-08 10:34:41
77	C073	M&C ELECTRONICS VINA COMPANY LIMITED	Mr. Manh	hrmctuyendung@gmail.com	097-1470487	Korea		Lot J1, Que Vo Industrial Park (expansion area) Phuong Lieu Commune, Que Vo District, Bac Ninh Province, Vietnam		active		2025-09-08 10:34:42	2025-09-08 10:34:42
78	C074	MOBASE VIETNAM COMPANY LIMITED	Mr. Tuan	batuan88gt@gmail.com	0357-080357	Korea		Yen Phong Industrial Park, Long Chau Commune, Yen Phong District, Bac Ninh Province, Vietnam		active		2025-09-08 10:34:43	2025-09-08 10:34:43
79	C075	NAM CHIEN CO., LTD	Mr. Nam	namchien1116@gmail.com;	096-4498540	Vietnam		Yen Nho Village, Gia Dong Commune, Thuan Thanh District, Bac Ninh Province		active		2025-09-08 10:34:44	2025-09-08 10:34:44
80	C076	TAN PHU PLASTIC BAC NINH CO.,LTD	Mr. Minh	taplast@tanphuplastic.com.vn	097-9958279	Vietnam		Tri Qua Industrial Cluster, Thuan Thanh Dist., Bac Ninh		active		2025-09-08 10:34:45	2025-09-08 10:34:45
81	C077	P&Q VINA ENGINEERING CO., LTD	Mr. Hung	vuhung86@gmail.com	0834-842255	Korea		Yen Phong Industrial Park, Long Chau Commune, Yen Phong District, Bac Ninh Province		active		2025-09-08 10:34:47	2025-09-08 10:34:47
82	C078	PNP VINA CO., LTD	Mr. Lee Jin Youl	info@pnpvietnam.com	973090992	Korea		Lot CN2-5, Que Vo Industrial Park III, Viet Hung Commune, Que Vo District, Bac Ninh Province, Vietnam		active		2025-09-08 10:34:48	2025-09-08 10:34:48
83	C079	QUANG AN CO., LTD	Mr. Nghia	nghia-quangan@gmail.com	098-9493768	Vietnam		Tan Hong - Hoan Son industrial cluster, Bu Lu village - Hoan Son - Tien Du-Bac Ninh		active		2025-09-08 10:34:49	2025-09-08 10:34:49
84	C080	RISHI VIET NAM COMPANY LIMITED	Ms Thuy	mould01@rishi.com.vn	096-8727061	Japan		Lot 4, Road TS6, Tien Son Industrial Park, Hoan Son Commune, Tien Du District, Bac Ninh Province, Vietnam		active		2025-09-08 10:34:50	2025-09-08 10:34:50
85	C081	SAMSUNG SDI VIETNAM CO., LTD	Mr. Lee See Hyung			Korea		Yen Phong I Industrial Park, Yen Trung Commune, Yen Phong District, Bac Ninh Province		active		2025-09-08 10:34:51	2025-09-08 10:34:51
86	C082	SENTEC HA NOI CO., LTD	Ms Phuong	ngophuong@gmail.com	091-4227785	Vietnam		Que Vo Industrial Park, Van Duong Ward, Bac Ninh City, Bac Ninh Province, Vietnam		active		2025-09-08 10:34:52	2025-09-08 10:34:52
87	C083	SEOJIN VINA COMPANY LIMITED	Ms Trang	seojinvina2@gmail.com	093-6854583	Korea		TS3 Road, Tien Son Industrial Park, Hoan Son Commune, Tien Du District, Bac Ninh Province, Vietnam		active		2025-09-08 10:34:54	2025-09-08 10:34:54
88	C084	SAMSUNG ELECTRONICS VIETNAM COMPANY LIMITED	Mr. Quyen	anh.quyen@samsung.com	094-1886391	Korea		Yen Phong Industrial Park, Long Chau Commune, Yen Phong District, Bac Ninh Province		active		2025-09-08 10:34:55	2025-09-08 10:34:55
89	C085	SI NETWORKS CO.,LTD	Mr Hoa	huyhoa.yuvi@gmail.com	097-3033909	vietnam		50, N3 Street - Residential and Commercial Service Complex, No. 16/9 Bui Van Ba Street, Tan Thuan Dong Ward, District 7, Ho Chi Minh City, Vietnam		active		2025-09-08 10:34:56	2025-09-08 10:34:56
90	C086	SKYTEC LIMITED LIABILITY COMPANY	Mr Cong	trantuan.acc01@gmail.com	039-7248802	Korea		Que Vo Industrial Park II, Ngoc Xa Commune, Que Vo District, Bac Ninh Province, Vietnam		active		2025-09-08 10:34:57	2025-09-08 10:34:57
91	C087	TAE GYEONG CO., LTD	Ms. Huong	huongnt27594@gmail.com	0352-276313	Vietnam		Khac Niem Industrial Cluster, Khac Niem Ward, Bac Ninh City, Bac Ninh Province		active		2025-09-08 10:34:58	2025-09-08 10:34:58
92	C088	TOYOPLAS MANUFACTURING（BAC GIANG）COMPANY LIMITED	Ms. Ngan	sunny.tan@toyoplasvn.com	0354-313666	Malaysia		Lot CN-04, Hoa Phu Industrial Park, Mai Dinh Commune, Hiep Hoa District, Bac Giang Province, Vietnam		active		2025-09-08 10:34:59	2025-09-08 10:34:59
93	C089	TVN PRECISION TRADING AND PROCESSING COMPANY LIMITED	Ms. Tuyen	tvn-ketoan@tvnmold.vn>	0365-859678	Vietnam		Mon Tu, Nam Son Ward, Bac Ninh City, Bac Ninh Province, Vietnam		active		2025-09-08 10:35:01	2025-09-08 10:35:01
94	C090	IU-TECH VIET NAM COMPANY LIMITED	Mr Hoa	iutechvina@gmail.com	093-1808333	Vietnam		Area 2, Dai Phuc Ward, Bac Ninh City, Bac Ninh Province, Vietnam		active		2025-09-08 10:35:02	2025-09-08 10:35:02
95	C091	WILLTECH VINA COMPANY LIMITED	Mr. Tuan	tranminhtb1981tuan@gmail.com	098-6076795	Korea		Lot D, Que Vo Industrial Park, Van Duong Ward, Bac Ninh City, Bac Ninh		active		2025-09-08 10:35:03	2025-09-08 10:35:03
96	C092	WONTECH VIETNAM COMPANY LIMITED	Mr Giap	phamgiapnb87@gmail.com	035-6351987	Korea		Lot C12, Dong Tho Multi-Career Industrial Cluster, Dong Tho Commune, Yen Phong District, Bac Ninh Province, Vietnam		active		2025-09-08 10:35:04	2025-09-08 10:35:04
\.


--
-- Data for Name: employees; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.employees (id, employee_id, name, english_name, email, phone, "position", department, hire_date, status, region, password, created_date, updated_date, gender, nationality, residence_country, city, address, birth_date, salary, salary_currency, driver_license, notes, work_status, access_level) FROM stdin;
31	2508002	LƯU THỊ HẰNG 	Luu Thi Hang	vietnam@yumold.com	+8498-983-0697	사원	총무	2025-08-01	active	베트남	$2b$12$nq4TmEUz7TV6/norUqDKOOdL/0pQXaqMK0zeXWfoZg9m7dPx.wTCW	2025-09-10 06:49:31	2025-09-10 08:52:21	여	베트남	베트남	박닌	Yên Trung – Yên Phong – Bắc Ninh	1997-07-15	18000000	VND	없음	\N	재직	master
32	2509001	NGUYỄN TRUNG THÀNH	NGUYEN TRUNG THANH	ymv-sale@yumold.com	+8496-942-3282	과장	기술	2025-09-08	active	한국	$2b$12$Y8Rei.R0wXoMngHJj342B.ROC1RwyfLFnZlQvgbK/Wmo6l7EruBSq	2025-09-10 07:46:57	2025-09-10 08:58:44	남	한국	베트남	박닌	Thôn Kim Phú, Xã Phong Doanh, Tỉnh Ninh Bình	1989-03-10	25000000	VND	있음		재직	user
27	2508001	김충성	KIM CHUNGSUNG	dave-vn@yumold.com	+8498-285-7582	대표	관리	2025-08-01	active	한국	$2b$12$m0ppfx4sSq0iF32.moDfzeIxBcEfVVKgV6bDQ8LCgQyM5VoDU/aFO	2025-09-10 06:24:48	2025-09-10 09:20:35.723719	남	한국	베트남	하노이	Sunshine City S1 Tower, Ciputra – Nam Thang Long, Dong Ngac Ward, Bac Tu Liem, Hanoi 11909, Vietnam	1982-11-24	2000000	VND	있음	\N	재직	master
\.


--
-- Data for Name: exchange_rates; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.exchange_rates (id, item_id, name, status, created_date, updated_date) FROM stdin;
\.


--
-- Data for Name: expense_requests; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.expense_requests (id, item_id, name, status, created_date, updated_date) FROM stdin;
\.


--
-- Data for Name: finished_products; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.finished_products (id, item_id, name, status, created_date, updated_date) FROM stdin;
\.


--
-- Data for Name: inventorys; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.inventorys (id, item_id, name, status, created_date, updated_date) FROM stdin;
\.


--
-- Data for Name: invoices; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.invoices (id, item_id, name, status, created_date, updated_date) FROM stdin;
\.


--
-- Data for Name: master_products; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.master_products (id, product_code, product_name, category, subcategory, hrct_code, hrcs_code, specification, unit, weight, dimensions, material, origin_country, manufacturer, model_number, certification, status, notes, created_date, updated_date) FROM stdin;
\.


--
-- Data for Name: monthly_saless; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.monthly_saless (id, item_id, name, status, created_date, updated_date) FROM stdin;
\.


--
-- Data for Name: notes; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.notes (id, item_id, name, status, created_date, updated_date) FROM stdin;
\.


--
-- Data for Name: notice_reads; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.notice_reads (id, read_id, notice_id, user_id, user_name, read_date) FROM stdin;
\.


--
-- Data for Name: notices; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.notices (id, item_id, name, status, created_date, updated_date, notice_id, title, content, category, priority, target_audience, department, author_id, author_name, publish_date, expire_date, is_pinned, view_count, attachments, tags, title_en, title_vi, content_en, content_vi) FROM stdin;
\.


--
-- Data for Name: order_items; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.order_items (id, order_id, item_number, product_name, product_code, specification, quantity, unit_price, total_price, unit, delivery_status, notes, created_date, updated_date) FROM stdin;
\.


--
-- Data for Name: orders; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.orders (id, order_id, quotation_id, customer_id, order_number, order_date, delivery_date, currency, exchange_rate, total_amount, status, notes, created_date, updated_date, customer_company_name, customer_contact_person, customer_email, customer_phone, customer_address, project_name, payment_terms, delivery_terms, sales_rep_name, sales_rep_email) FROM stdin;
\.


--
-- Data for Name: product_codes; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.product_codes (id, item_id, name, status, created_date, updated_date) FROM stdin;
\.


--
-- Data for Name: products; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.products (id, product_id, product_name, product_code, category, subcategory, specification, unit, standard_price, currency, supplier_id, lead_time, status, notes, created_date, updated_date) FROM stdin;
\.


--
-- Data for Name: quotation_items; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.quotation_items (id, quotation_id, item_number, product_name, product_code, specification, quantity, unit_price, total_price, unit, lead_time, notes, created_date, updated_date) FROM stdin;
\.


--
-- Data for Name: quotations; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.quotations (id, quotation_id, customer_id, quotation_number, quotation_date, delivery_date, currency, exchange_rate, total_amount, status, notes, created_date, updated_date, revision_number, original_quotation_id, project_name, project_description, payment_terms, validity_period, delivery_terms, sales_rep_name, sales_rep_email, customer_company_name, customer_contact_person, customer_email, customer_phone, customer_address) FROM stdin;
\.


--
-- Data for Name: sales_products; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.sales_products (id, item_id, name, status, created_date, updated_date) FROM stdin;
\.


--
-- Data for Name: shippings; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.shippings (id, item_id, name, status, created_date, updated_date) FROM stdin;
\.


--
-- Data for Name: suppliers; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.suppliers (id, supplier_id, company_name, contact_person, email, phone, address, country, city, business_type, payment_terms, credit_limit, currency, status, notes, created_date, updated_date) FROM stdin;
\.


--
-- Data for Name: system_config_history; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.system_config_history (id, history_id, config_key, old_value, new_value, change_reason, changed_by, changed_date) FROM stdin;
\.


--
-- Data for Name: system_configs; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.system_configs (id, item_id, name, status, created_date, updated_date) FROM stdin;
\.


--
-- Data for Name: user_notes; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.user_notes (note_id, user_id, page_name, note_content, created_date, updated_date) FROM stdin;
\.


--
-- Data for Name: user_sessions; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.user_sessions (id, session_id, user_id, created_date, expires_date, is_active) FROM stdin;
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.users (id, user_id, username, email, password_hash, access_level, is_active, last_login, created_date, updated_date) FROM stdin;
\.


--
-- Data for Name: vacations; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.vacations (id, item_id, name, status, created_date, updated_date) FROM stdin;
\.


--
-- Data for Name: weekly_reports; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.weekly_reports (id, item_id, name, status, created_date, updated_date) FROM stdin;
\.


--
-- Data for Name: work_statuss; Type: TABLE DATA; Schema: public; Owner: neondb_owner
--

COPY public.work_statuss (id, item_id, name, status, created_date, updated_date) FROM stdin;
\.


--
-- Name: approval_history_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.approval_history_id_seq', 1, false);


--
-- Name: approval_requests_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.approval_requests_id_seq', 1, false);


--
-- Name: business_processs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.business_processs_id_seq', 1, false);


--
-- Name: cash_flows_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.cash_flows_id_seq', 1, false);


--
-- Name: cash_transactions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.cash_transactions_id_seq', 1, false);


--
-- Name: customers_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.customers_id_seq', 96, true);


--
-- Name: employees_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.employees_id_seq', 36, true);


--
-- Name: exchange_rates_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.exchange_rates_id_seq', 1, false);


--
-- Name: expense_requests_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.expense_requests_id_seq', 1, false);


--
-- Name: finished_products_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.finished_products_id_seq', 1, false);


--
-- Name: inventorys_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.inventorys_id_seq', 1, false);


--
-- Name: invoices_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.invoices_id_seq', 1, false);


--
-- Name: master_products_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.master_products_id_seq', 1, false);


--
-- Name: monthly_saless_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.monthly_saless_id_seq', 1, false);


--
-- Name: notes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.notes_id_seq', 1, false);


--
-- Name: notice_reads_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.notice_reads_id_seq', 1, false);


--
-- Name: notices_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.notices_id_seq', 1, false);


--
-- Name: order_items_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.order_items_id_seq', 4, true);


--
-- Name: orders_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.orders_id_seq', 2, true);


--
-- Name: product_codes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.product_codes_id_seq', 1, false);


--
-- Name: products_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.products_id_seq', 1, false);


--
-- Name: quotation_items_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.quotation_items_id_seq', 4, true);


--
-- Name: quotations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.quotations_id_seq', 2, true);


--
-- Name: sales_products_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.sales_products_id_seq', 1, false);


--
-- Name: shippings_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.shippings_id_seq', 1, false);


--
-- Name: suppliers_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.suppliers_id_seq', 1, false);


--
-- Name: system_config_history_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.system_config_history_id_seq', 1, false);


--
-- Name: system_configs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.system_configs_id_seq', 1, false);


--
-- Name: user_sessions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.user_sessions_id_seq', 1, false);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.users_id_seq', 1, false);


--
-- Name: vacations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.vacations_id_seq', 1, false);


--
-- Name: weekly_reports_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.weekly_reports_id_seq', 1, false);


--
-- Name: work_statuss_id_seq; Type: SEQUENCE SET; Schema: public; Owner: neondb_owner
--

SELECT pg_catalog.setval('public.work_statuss_id_seq', 1, false);


--
-- Name: approval_history approval_history_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.approval_history
    ADD CONSTRAINT approval_history_pkey PRIMARY KEY (id);


--
-- Name: approval_requests approval_requests_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.approval_requests
    ADD CONSTRAINT approval_requests_pkey PRIMARY KEY (id);


--
-- Name: approval_requests approval_requests_request_id_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.approval_requests
    ADD CONSTRAINT approval_requests_request_id_key UNIQUE (request_id);


--
-- Name: business_processs business_processs_item_id_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.business_processs
    ADD CONSTRAINT business_processs_item_id_key UNIQUE (item_id);


--
-- Name: business_processs business_processs_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.business_processs
    ADD CONSTRAINT business_processs_pkey PRIMARY KEY (id);


--
-- Name: cash_flows cash_flows_item_id_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.cash_flows
    ADD CONSTRAINT cash_flows_item_id_key UNIQUE (item_id);


--
-- Name: cash_flows cash_flows_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.cash_flows
    ADD CONSTRAINT cash_flows_pkey PRIMARY KEY (id);


--
-- Name: cash_transactions cash_transactions_item_id_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.cash_transactions
    ADD CONSTRAINT cash_transactions_item_id_key UNIQUE (item_id);


--
-- Name: cash_transactions cash_transactions_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.cash_transactions
    ADD CONSTRAINT cash_transactions_pkey PRIMARY KEY (id);


--
-- Name: customers customers_customer_id_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.customers
    ADD CONSTRAINT customers_customer_id_key UNIQUE (customer_id);


--
-- Name: customers customers_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.customers
    ADD CONSTRAINT customers_pkey PRIMARY KEY (id);


--
-- Name: employees employees_employee_id_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.employees
    ADD CONSTRAINT employees_employee_id_key UNIQUE (employee_id);


--
-- Name: employees employees_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.employees
    ADD CONSTRAINT employees_pkey PRIMARY KEY (id);


--
-- Name: exchange_rates exchange_rates_item_id_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.exchange_rates
    ADD CONSTRAINT exchange_rates_item_id_key UNIQUE (item_id);


--
-- Name: exchange_rates exchange_rates_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.exchange_rates
    ADD CONSTRAINT exchange_rates_pkey PRIMARY KEY (id);


--
-- Name: expense_requests expense_requests_item_id_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.expense_requests
    ADD CONSTRAINT expense_requests_item_id_key UNIQUE (item_id);


--
-- Name: expense_requests expense_requests_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.expense_requests
    ADD CONSTRAINT expense_requests_pkey PRIMARY KEY (id);


--
-- Name: finished_products finished_products_item_id_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.finished_products
    ADD CONSTRAINT finished_products_item_id_key UNIQUE (item_id);


--
-- Name: finished_products finished_products_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.finished_products
    ADD CONSTRAINT finished_products_pkey PRIMARY KEY (id);


--
-- Name: inventorys inventorys_item_id_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.inventorys
    ADD CONSTRAINT inventorys_item_id_key UNIQUE (item_id);


--
-- Name: inventorys inventorys_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.inventorys
    ADD CONSTRAINT inventorys_pkey PRIMARY KEY (id);


--
-- Name: invoices invoices_item_id_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.invoices
    ADD CONSTRAINT invoices_item_id_key UNIQUE (item_id);


--
-- Name: invoices invoices_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.invoices
    ADD CONSTRAINT invoices_pkey PRIMARY KEY (id);


--
-- Name: master_products master_products_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.master_products
    ADD CONSTRAINT master_products_pkey PRIMARY KEY (id);


--
-- Name: master_products master_products_product_code_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.master_products
    ADD CONSTRAINT master_products_product_code_key UNIQUE (product_code);


--
-- Name: monthly_saless monthly_saless_item_id_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.monthly_saless
    ADD CONSTRAINT monthly_saless_item_id_key UNIQUE (item_id);


--
-- Name: monthly_saless monthly_saless_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.monthly_saless
    ADD CONSTRAINT monthly_saless_pkey PRIMARY KEY (id);


--
-- Name: notes notes_item_id_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.notes
    ADD CONSTRAINT notes_item_id_key UNIQUE (item_id);


--
-- Name: notes notes_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.notes
    ADD CONSTRAINT notes_pkey PRIMARY KEY (id);


--
-- Name: notice_reads notice_reads_notice_id_user_id_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.notice_reads
    ADD CONSTRAINT notice_reads_notice_id_user_id_key UNIQUE (notice_id, user_id);


--
-- Name: notice_reads notice_reads_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.notice_reads
    ADD CONSTRAINT notice_reads_pkey PRIMARY KEY (id);


--
-- Name: notice_reads notice_reads_read_id_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.notice_reads
    ADD CONSTRAINT notice_reads_read_id_key UNIQUE (read_id);


--
-- Name: notices notices_item_id_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.notices
    ADD CONSTRAINT notices_item_id_key UNIQUE (item_id);


--
-- Name: notices notices_notice_id_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.notices
    ADD CONSTRAINT notices_notice_id_key UNIQUE (notice_id);


--
-- Name: notices notices_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.notices
    ADD CONSTRAINT notices_pkey PRIMARY KEY (id);


--
-- Name: order_items order_items_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.order_items
    ADD CONSTRAINT order_items_pkey PRIMARY KEY (id);


--
-- Name: orders orders_order_id_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_order_id_key UNIQUE (order_id);


--
-- Name: orders orders_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.orders
    ADD CONSTRAINT orders_pkey PRIMARY KEY (id);


--
-- Name: product_codes product_codes_item_id_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.product_codes
    ADD CONSTRAINT product_codes_item_id_key UNIQUE (item_id);


--
-- Name: product_codes product_codes_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.product_codes
    ADD CONSTRAINT product_codes_pkey PRIMARY KEY (id);


--
-- Name: products products_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.products
    ADD CONSTRAINT products_pkey PRIMARY KEY (id);


--
-- Name: products products_product_code_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.products
    ADD CONSTRAINT products_product_code_key UNIQUE (product_code);


--
-- Name: products products_product_id_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.products
    ADD CONSTRAINT products_product_id_key UNIQUE (product_id);


--
-- Name: quotation_items quotation_items_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.quotation_items
    ADD CONSTRAINT quotation_items_pkey PRIMARY KEY (id);


--
-- Name: quotations quotations_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.quotations
    ADD CONSTRAINT quotations_pkey PRIMARY KEY (id);


--
-- Name: quotations quotations_quotation_id_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.quotations
    ADD CONSTRAINT quotations_quotation_id_key UNIQUE (quotation_id);


--
-- Name: sales_products sales_products_item_id_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.sales_products
    ADD CONSTRAINT sales_products_item_id_key UNIQUE (item_id);


--
-- Name: sales_products sales_products_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.sales_products
    ADD CONSTRAINT sales_products_pkey PRIMARY KEY (id);


--
-- Name: shippings shippings_item_id_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.shippings
    ADD CONSTRAINT shippings_item_id_key UNIQUE (item_id);


--
-- Name: shippings shippings_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.shippings
    ADD CONSTRAINT shippings_pkey PRIMARY KEY (id);


--
-- Name: suppliers suppliers_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.suppliers
    ADD CONSTRAINT suppliers_pkey PRIMARY KEY (id);


--
-- Name: suppliers suppliers_supplier_id_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.suppliers
    ADD CONSTRAINT suppliers_supplier_id_key UNIQUE (supplier_id);


--
-- Name: system_config_history system_config_history_history_id_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.system_config_history
    ADD CONSTRAINT system_config_history_history_id_key UNIQUE (history_id);


--
-- Name: system_config_history system_config_history_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.system_config_history
    ADD CONSTRAINT system_config_history_pkey PRIMARY KEY (id);


--
-- Name: system_configs system_configs_item_id_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.system_configs
    ADD CONSTRAINT system_configs_item_id_key UNIQUE (item_id);


--
-- Name: system_configs system_configs_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.system_configs
    ADD CONSTRAINT system_configs_pkey PRIMARY KEY (id);


--
-- Name: user_notes user_notes_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.user_notes
    ADD CONSTRAINT user_notes_pkey PRIMARY KEY (note_id);


--
-- Name: user_notes user_notes_user_id_page_name_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.user_notes
    ADD CONSTRAINT user_notes_user_id_page_name_key UNIQUE (user_id, page_name);


--
-- Name: user_sessions user_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.user_sessions
    ADD CONSTRAINT user_sessions_pkey PRIMARY KEY (id);


--
-- Name: user_sessions user_sessions_session_id_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.user_sessions
    ADD CONSTRAINT user_sessions_session_id_key UNIQUE (session_id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: users users_user_id_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_user_id_key UNIQUE (user_id);


--
-- Name: users users_username_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_username_key UNIQUE (username);


--
-- Name: vacations vacations_item_id_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.vacations
    ADD CONSTRAINT vacations_item_id_key UNIQUE (item_id);


--
-- Name: vacations vacations_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.vacations
    ADD CONSTRAINT vacations_pkey PRIMARY KEY (id);


--
-- Name: weekly_reports weekly_reports_item_id_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.weekly_reports
    ADD CONSTRAINT weekly_reports_item_id_key UNIQUE (item_id);


--
-- Name: weekly_reports weekly_reports_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.weekly_reports
    ADD CONSTRAINT weekly_reports_pkey PRIMARY KEY (id);


--
-- Name: work_statuss work_statuss_item_id_key; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.work_statuss
    ADD CONSTRAINT work_statuss_item_id_key UNIQUE (item_id);


--
-- Name: work_statuss work_statuss_pkey; Type: CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.work_statuss
    ADD CONSTRAINT work_statuss_pkey PRIMARY KEY (id);


--
-- Name: idx_customers_company_name; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX idx_customers_company_name ON public.customers USING btree (company_name);


--
-- Name: idx_customers_country; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX idx_customers_country ON public.customers USING btree (country);


--
-- Name: idx_customers_customer_id; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX idx_customers_customer_id ON public.customers USING btree (customer_id);


--
-- Name: idx_customers_status; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX idx_customers_status ON public.customers USING btree (status);


--
-- Name: idx_employees_department; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX idx_employees_department ON public.employees USING btree (department);


--
-- Name: idx_employees_employee_id; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX idx_employees_employee_id ON public.employees USING btree (employee_id);


--
-- Name: idx_employees_name; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX idx_employees_name ON public.employees USING btree (name);


--
-- Name: idx_employees_region; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX idx_employees_region ON public.employees USING btree (region);


--
-- Name: idx_employees_status; Type: INDEX; Schema: public; Owner: neondb_owner
--

CREATE INDEX idx_employees_status ON public.employees USING btree (status);


--
-- Name: approval_history approval_history_request_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.approval_history
    ADD CONSTRAINT approval_history_request_id_fkey FOREIGN KEY (request_id) REFERENCES public.approval_requests(request_id) ON DELETE CASCADE;


--
-- Name: order_items order_items_order_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.order_items
    ADD CONSTRAINT order_items_order_id_fkey FOREIGN KEY (order_id) REFERENCES public.orders(order_id);


--
-- Name: user_sessions user_sessions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: neondb_owner
--

ALTER TABLE ONLY public.user_sessions
    ADD CONSTRAINT user_sessions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE;


--
-- Name: DEFAULT PRIVILEGES FOR SEQUENCES; Type: DEFAULT ACL; Schema: public; Owner: cloud_admin
--

ALTER DEFAULT PRIVILEGES FOR ROLE cloud_admin IN SCHEMA public GRANT ALL ON SEQUENCES TO neon_superuser WITH GRANT OPTION;


--
-- Name: DEFAULT PRIVILEGES FOR TABLES; Type: DEFAULT ACL; Schema: public; Owner: cloud_admin
--

ALTER DEFAULT PRIVILEGES FOR ROLE cloud_admin IN SCHEMA public GRANT ALL ON TABLES TO neon_superuser WITH GRANT OPTION;


--
-- PostgreSQL database dump complete
--

