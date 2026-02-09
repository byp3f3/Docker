--
-- PostgreSQL database dump
--

\restrict zvzxXLWDd7FnQJVHT6Mb42qXih8RKDaYaVOUaMX0MGYqpDHxQq1nDuGlxQz79Ob

-- Dumped from database version 17.6
-- Dumped by pg_dump version 17.6

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: fn_audit_log(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.fn_audit_log() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_action     VARCHAR(100);
    v_record_id  BIGINT;
    v_user_id    BIGINT;
    v_old_values JSONB := NULL;
    v_new_values JSONB := NULL;
BEGIN
    -- Определить тип операции
    IF TG_OP = 'INSERT' THEN
        v_action := 'CREATE';
    ELSIF TG_OP = 'UPDATE' THEN
        v_action := 'UPDATE';
    ELSIF TG_OP = 'DELETE' THEN
        v_action := 'DELETE';
    END IF;

    -- Получить ID записи и значения
    IF TG_OP = 'DELETE' THEN
        v_old_values := to_jsonb(OLD);
        v_record_id  := OLD."productId";  -- будет перезаписан ниже для каждой таблицы
    ELSE
        v_new_values := to_jsonb(NEW);
    END IF;

    IF TG_OP IN ('UPDATE') THEN
        v_old_values := to_jsonb(OLD);
    END IF;

    -- Определить ID записи в зависимости от таблицы
    CASE TG_TABLE_NAME
        WHEN 'product' THEN
            v_record_id := COALESCE(NEW."productId", OLD."productId");
        WHEN 'order' THEN
            v_record_id := COALESCE(NEW."orderId", OLD."orderId");
        WHEN 'user' THEN
            v_record_id := COALESCE(NEW."userId", OLD."userId");
        ELSE
            v_record_id := 0;
    END CASE;

    -- Получить ID пользователя из сессии (устанавливается Django)
    BEGIN
        v_user_id := current_setting('app.current_user_id')::BIGINT;
    EXCEPTION WHEN OTHERS THEN
        -- Если переменная не установлена, пытаемся взять из записи
        IF TG_TABLE_NAME = 'order' THEN
            v_user_id := COALESCE(NEW."userId", OLD."userId");
        ELSIF TG_TABLE_NAME = 'user' THEN
            v_user_id := COALESCE(NEW."userId", OLD."userId");
        ELSE
            v_user_id := 1;  -- системный пользователь по умолчанию
        END IF;
    END;

    -- Записать в журнал аудита
    INSERT INTO "auditLog" ("userId", "action", "tableName", "recordId",
                            "oldValues", "newValues", "createdAt")
    VALUES (v_user_id, v_action, TG_TABLE_NAME, v_record_id,
            v_old_values, v_new_values, NOW());

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    ELSE
        RETURN NEW;
    END IF;
END;
$$;


ALTER FUNCTION public.fn_audit_log() OWNER TO postgres;

--
-- Name: fn_review_update_timestamp(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.fn_review_update_timestamp() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW."updatedAt" := NOW();
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.fn_review_update_timestamp() OWNER TO postgres;

--
-- Name: sp_adjust_prices_by_category(integer, numeric); Type: PROCEDURE; Schema: public; Owner: postgres
--

CREATE PROCEDURE public.sp_adjust_prices_by_category(IN p_category_id integer, IN p_percent_change numeric)
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_affected INTEGER;
BEGIN
    IF p_percent_change < -90 OR p_percent_change > 500 THEN
        RAISE EXCEPTION 'Процент изменения должен быть от -90%% до 500%%';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM "category" WHERE "categoryId" = p_category_id) THEN
        RAISE EXCEPTION 'Категория с ID = % не найдена', p_category_id;
    END IF;

    UPDATE "product"
    SET "price" = ROUND("price" * (1 + p_percent_change / 100.0), 2)
    WHERE "categoryId" = p_category_id;

    GET DIAGNOSTICS v_affected = ROW_COUNT;

    RAISE NOTICE 'Цены обновлены для % товаров в категории %', v_affected, p_category_id;
END;
$$;


ALTER PROCEDURE public.sp_adjust_prices_by_category(IN p_category_id integer, IN p_percent_change numeric) OWNER TO postgres;

--
-- Name: sp_cancel_order(bigint); Type: PROCEDURE; Schema: public; Owner: postgres
--

CREATE PROCEDURE public.sp_cancel_order(IN p_order_id bigint)
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_current_status VARCHAR(100);
    v_payment_status VARCHAR(30);
    v_cancel_status_id INTEGER;
    v_item RECORD;
BEGIN
    -- Получить текущий статус заказа
    SELECT os."orderStatusName", o."paymentStatus"
    INTO v_current_status, v_payment_status
    FROM "order" o
        JOIN "orderStatus" os ON o."orderStatusId" = os."orderStatusId"
    WHERE o."orderId" = p_order_id;

    IF v_current_status IS NULL THEN
        RAISE EXCEPTION 'Заказ #% не найден', p_order_id;
    END IF;

    IF v_current_status = 'Отменен' THEN
        RAISE EXCEPTION 'Заказ #% уже отменён', p_order_id;
    END IF;

    IF v_current_status = 'Доставлен' THEN
        RAISE EXCEPTION 'Нельзя отменить доставленный заказ #%', p_order_id;
    END IF;

    -- Получить ID статуса «Отменен»
    SELECT "orderStatusId" INTO v_cancel_status_id
    FROM "orderStatus" WHERE "orderStatusName" = 'Отменен';

    -- Вернуть товары на склад
    FOR v_item IN
        SELECT "productId", "quantity"
        FROM "orderItem"
        WHERE "orderId" = p_order_id
    LOOP
        UPDATE "product"
        SET "quantity" = "quantity" + v_item."quantity"
        WHERE "productId" = v_item."productId";
    END LOOP;

    -- Обновить заказ
    UPDATE "order"
    SET "orderStatusId" = v_cancel_status_id,
        "paymentStatus" = CASE
            WHEN "paymentStatus" = 'оплачено' THEN 'возврат средств'
            ELSE "paymentStatus"
        END
    WHERE "orderId" = p_order_id;
END;
$$;


ALTER PROCEDURE public.sp_cancel_order(IN p_order_id bigint) OWNER TO postgres;

--
-- Name: sp_create_order_from_cart(bigint, bigint, character varying, character varying); Type: PROCEDURE; Schema: public; Owner: postgres
--

CREATE PROCEDURE public.sp_create_order_from_cart(IN p_user_id bigint, IN p_address_id bigint, IN p_delivery_type character varying, IN p_payment_type character varying)
    LANGUAGE plpgsql
    AS $$
DECLARE
    v_order_id     BIGINT;
    v_total        NUMERIC(10,2) := 0;
    v_status_id    INTEGER;
    v_cart_item    RECORD;
    v_product_qty  INTEGER;
BEGIN
    -- Проверка: корзина не пуста
    IF NOT EXISTS (SELECT 1 FROM "cart" WHERE "userId" = p_user_id) THEN
        RAISE EXCEPTION 'Корзина пользователя пуста';
    END IF;

    -- Проверка наличия товаров на складе
    FOR v_cart_item IN
        SELECT c."productId", c."quantity", p."productName", p."quantity" AS "stock"
        FROM "cart" c
            JOIN "product" p ON c."productId" = p."productId"
        WHERE c."userId" = p_user_id
    LOOP
        IF v_cart_item."stock" < v_cart_item."quantity" THEN
            RAISE EXCEPTION 'Недостаточно товара "%" на складе (в наличии: %, запрошено: %)',
                v_cart_item."productName", v_cart_item."stock", v_cart_item."quantity";
        END IF;
    END LOOP;

    -- Получить статус «Новый»
    SELECT "orderStatusId" INTO v_status_id
    FROM "orderStatus" WHERE "orderStatusName" = 'Новый';

    -- Рассчитать итог
    SELECT SUM(c."quantity" * p."price") INTO v_total
    FROM "cart" c
        JOIN "product" p ON c."productId" = p."productId"
    WHERE c."userId" = p_user_id;

    -- Создать заказ
    INSERT INTO "order" ("userId", "orderStatusId", "total", "addressId",
                         "deliveryType", "paymentType", "paymentStatus", "createdAt")
    VALUES (p_user_id, v_status_id, v_total, p_address_id,
            p_delivery_type, p_payment_type, 'ждет оплаты', NOW())
    RETURNING "orderId" INTO v_order_id;

    -- Перенести позиции из корзины в заказ и уменьшить остатки
    FOR v_cart_item IN
        SELECT c."productId", c."quantity", p."price"
        FROM "cart" c
            JOIN "product" p ON c."productId" = p."productId"
        WHERE c."userId" = p_user_id
    LOOP
        INSERT INTO "orderItem" ("orderId", "productId", "quantity", "unitPrice")
        VALUES (v_order_id, v_cart_item."productId",
                v_cart_item."quantity", v_cart_item."price");

        UPDATE "product"
        SET "quantity" = "quantity" - v_cart_item."quantity"
        WHERE "productId" = v_cart_item."productId";
    END LOOP;

    -- Очистить корзину
    DELETE FROM "cart" WHERE "userId" = p_user_id;
END;
$$;


ALTER PROCEDURE public.sp_create_order_from_cart(IN p_user_id bigint, IN p_address_id bigint, IN p_delivery_type character varying, IN p_payment_type character varying) OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: address; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.address (
    "addressId" bigint NOT NULL,
    "userId" bigint NOT NULL,
    city character varying(100) NOT NULL,
    street character varying(100) NOT NULL,
    house character varying(50) NOT NULL,
    flat character varying(10),
    index character varying(6) NOT NULL,
    CONSTRAINT address_index_check CHECK (((index)::text ~ '^[0-9]{6}$'::text))
);


ALTER TABLE public.address OWNER TO postgres;

--
-- Name: address_addressId_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public."address_addressId_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public."address_addressId_seq" OWNER TO postgres;

--
-- Name: address_addressId_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public."address_addressId_seq" OWNED BY public.address."addressId";


--
-- Name: auditLog; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public."auditLog" (
    "auditLogId" bigint NOT NULL,
    "userId" bigint NOT NULL,
    action character varying(100) NOT NULL,
    "tableName" character varying(100) NOT NULL,
    "recordId" bigint NOT NULL,
    "oldValues" jsonb,
    "newValues" jsonb,
    "createdAt" timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT "auditLog_action_check" CHECK (((action)::text = ANY ((ARRAY['CREATE'::character varying, 'UPDATE'::character varying, 'DELETE'::character varying])::text[])))
);


ALTER TABLE public."auditLog" OWNER TO postgres;

--
-- Name: auditLog_auditLogId_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public."auditLog_auditLogId_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public."auditLog_auditLogId_seq" OWNER TO postgres;

--
-- Name: auditLog_auditLogId_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public."auditLog_auditLogId_seq" OWNED BY public."auditLog"."auditLogId";


--
-- Name: auth_group; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.auth_group (
    id integer NOT NULL,
    name character varying(150) NOT NULL
);


ALTER TABLE public.auth_group OWNER TO postgres;

--
-- Name: auth_group_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.auth_group ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.auth_group_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: auth_group_permissions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.auth_group_permissions (
    id bigint NOT NULL,
    group_id integer NOT NULL,
    permission_id integer NOT NULL
);


ALTER TABLE public.auth_group_permissions OWNER TO postgres;

--
-- Name: auth_group_permissions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.auth_group_permissions ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.auth_group_permissions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: auth_permission; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.auth_permission (
    id integer NOT NULL,
    name character varying(255) NOT NULL,
    content_type_id integer NOT NULL,
    codename character varying(100) NOT NULL
);


ALTER TABLE public.auth_permission OWNER TO postgres;

--
-- Name: auth_permission_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.auth_permission ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.auth_permission_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: authtoken_token; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.authtoken_token (
    key character varying(40) NOT NULL,
    created timestamp with time zone NOT NULL,
    user_id bigint NOT NULL
);


ALTER TABLE public.authtoken_token OWNER TO postgres;

--
-- Name: brand; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.brand (
    "brandId" integer NOT NULL,
    "brandName" character varying(100) NOT NULL,
    "brandDescription" text NOT NULL,
    "brandCountry" character varying(100) NOT NULL
);


ALTER TABLE public.brand OWNER TO postgres;

--
-- Name: brand_brandId_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public."brand_brandId_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public."brand_brandId_seq" OWNER TO postgres;

--
-- Name: brand_brandId_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public."brand_brandId_seq" OWNED BY public.brand."brandId";


--
-- Name: cart; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.cart (
    "cartId" bigint NOT NULL,
    "userId" bigint NOT NULL,
    "productId" bigint NOT NULL,
    quantity integer NOT NULL,
    CONSTRAINT cart_quantity_check CHECK ((quantity > 0))
);


ALTER TABLE public.cart OWNER TO postgres;

--
-- Name: cart_cartId_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public."cart_cartId_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public."cart_cartId_seq" OWNER TO postgres;

--
-- Name: cart_cartId_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public."cart_cartId_seq" OWNED BY public.cart."cartId";


--
-- Name: category; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.category (
    "categoryId" integer NOT NULL,
    "categoryName" character varying(100) NOT NULL,
    "categoryDescription" text NOT NULL
);


ALTER TABLE public.category OWNER TO postgres;

--
-- Name: category_categoryId_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public."category_categoryId_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public."category_categoryId_seq" OWNER TO postgres;

--
-- Name: category_categoryId_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public."category_categoryId_seq" OWNED BY public.category."categoryId";


--
-- Name: django_admin_log; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.django_admin_log (
    id integer NOT NULL,
    action_time timestamp with time zone NOT NULL,
    object_id text,
    object_repr character varying(200) NOT NULL,
    action_flag smallint NOT NULL,
    change_message text NOT NULL,
    content_type_id integer,
    user_id bigint NOT NULL,
    CONSTRAINT django_admin_log_action_flag_check CHECK ((action_flag >= 0))
);


ALTER TABLE public.django_admin_log OWNER TO postgres;

--
-- Name: django_admin_log_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.django_admin_log ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.django_admin_log_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: django_content_type; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.django_content_type (
    id integer NOT NULL,
    app_label character varying(100) NOT NULL,
    model character varying(100) NOT NULL
);


ALTER TABLE public.django_content_type OWNER TO postgres;

--
-- Name: django_content_type_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.django_content_type ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.django_content_type_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: django_migrations; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.django_migrations (
    id bigint NOT NULL,
    app character varying(255) NOT NULL,
    name character varying(255) NOT NULL,
    applied timestamp with time zone NOT NULL
);


ALTER TABLE public.django_migrations OWNER TO postgres;

--
-- Name: django_migrations_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

ALTER TABLE public.django_migrations ALTER COLUMN id ADD GENERATED BY DEFAULT AS IDENTITY (
    SEQUENCE NAME public.django_migrations_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: django_session; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.django_session (
    session_key character varying(40) NOT NULL,
    session_data text NOT NULL,
    expire_date timestamp with time zone NOT NULL
);


ALTER TABLE public.django_session OWNER TO postgres;

--
-- Name: order; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public."order" (
    "orderId" bigint NOT NULL,
    "userId" bigint NOT NULL,
    "orderStatusId" integer NOT NULL,
    total numeric(10,2) NOT NULL,
    "addressId" bigint NOT NULL,
    "deliveryType" character varying(20) NOT NULL,
    "paymentType" character varying(30) NOT NULL,
    "paymentStatus" character varying(30) NOT NULL,
    note character varying(100),
    "createdAt" timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT "order_deliveryType_check" CHECK ((("deliveryType")::text = ANY ((ARRAY['самовывоз'::character varying, 'пункт выдачи'::character varying, 'курьером'::character varying])::text[]))),
    CONSTRAINT "order_paymentStatus_check" CHECK ((("paymentStatus")::text = ANY ((ARRAY['ждет оплаты'::character varying, 'оплачено'::character varying, 'возврат средств'::character varying, 'средства возвращены'::character varying])::text[]))),
    CONSTRAINT "order_paymentType_check" CHECK ((("paymentType")::text = ANY ((ARRAY['онлайн'::character varying, 'картой при получении'::character varying, 'наличными при получении'::character varying])::text[]))),
    CONSTRAINT order_total_check CHECK ((total >= (0)::numeric))
);


ALTER TABLE public."order" OWNER TO postgres;

--
-- Name: orderItem; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public."orderItem" (
    "orderItemId" bigint NOT NULL,
    "orderId" bigint NOT NULL,
    "productId" bigint NOT NULL,
    quantity integer NOT NULL,
    "unitPrice" numeric(10,2) NOT NULL,
    CONSTRAINT "orderItem_quantity_check" CHECK ((quantity > 0)),
    CONSTRAINT "orderItem_unitPrice_check" CHECK (("unitPrice" > (0)::numeric))
);


ALTER TABLE public."orderItem" OWNER TO postgres;

--
-- Name: orderItem_orderItemId_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public."orderItem_orderItemId_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public."orderItem_orderItemId_seq" OWNER TO postgres;

--
-- Name: orderItem_orderItemId_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public."orderItem_orderItemId_seq" OWNED BY public."orderItem"."orderItemId";


--
-- Name: orderStatus; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public."orderStatus" (
    "orderStatusId" integer NOT NULL,
    "orderStatusName" character varying(100) NOT NULL
);


ALTER TABLE public."orderStatus" OWNER TO postgres;

--
-- Name: orderStatus_orderStatusId_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public."orderStatus_orderStatusId_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public."orderStatus_orderStatusId_seq" OWNER TO postgres;

--
-- Name: orderStatus_orderStatusId_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public."orderStatus_orderStatusId_seq" OWNED BY public."orderStatus"."orderStatusId";


--
-- Name: order_orderId_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public."order_orderId_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public."order_orderId_seq" OWNER TO postgres;

--
-- Name: order_orderId_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public."order_orderId_seq" OWNED BY public."order"."orderId";


--
-- Name: parentChild; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public."parentChild" (
    "parentChildId" bigint NOT NULL,
    "userId" bigint NOT NULL,
    "childId" bigint NOT NULL
);


ALTER TABLE public."parentChild" OWNER TO postgres;

--
-- Name: parentChild_parentChildId_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public."parentChild_parentChildId_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public."parentChild_parentChildId_seq" OWNER TO postgres;

--
-- Name: parentChild_parentChildId_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public."parentChild_parentChildId_seq" OWNED BY public."parentChild"."parentChildId";


--
-- Name: product; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.product (
    "productId" bigint NOT NULL,
    "productName" character varying(100) NOT NULL,
    "productDescription" text NOT NULL,
    "categoryId" integer NOT NULL,
    "brandId" integer NOT NULL,
    price numeric(10,2) NOT NULL,
    "ageRating" integer NOT NULL,
    quantity integer NOT NULL,
    "weightKg" numeric(10,2) NOT NULL,
    dimensions character varying(50) NOT NULL,
    CONSTRAINT "product_ageRating_check" CHECK (("ageRating" >= 0)),
    CONSTRAINT product_price_check CHECK ((price > (0)::numeric)),
    CONSTRAINT product_quantity_check CHECK ((quantity >= 0)),
    CONSTRAINT "product_weightKg_check" CHECK (("weightKg" > (0)::numeric))
);


ALTER TABLE public.product OWNER TO postgres;

--
-- Name: productAttribute; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public."productAttribute" (
    "productAttributeId" bigint NOT NULL,
    "productId" bigint NOT NULL,
    "productAttributeName" character varying(100) NOT NULL,
    "productAttributeValue" character varying(100) NOT NULL,
    "productAttributeUnit" character varying(50)
);


ALTER TABLE public."productAttribute" OWNER TO postgres;

--
-- Name: productAttribute_productAttributeId_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public."productAttribute_productAttributeId_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public."productAttribute_productAttributeId_seq" OWNER TO postgres;

--
-- Name: productAttribute_productAttributeId_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public."productAttribute_productAttributeId_seq" OWNED BY public."productAttribute"."productAttributeId";


--
-- Name: productImage; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public."productImage" (
    "productImageId" bigint NOT NULL,
    "productId" bigint NOT NULL,
    url character varying(500) NOT NULL,
    "altText" character varying(100) NOT NULL,
    "isMain" boolean DEFAULT false NOT NULL
);


ALTER TABLE public."productImage" OWNER TO postgres;

--
-- Name: productImage_productImageId_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public."productImage_productImageId_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public."productImage_productImageId_seq" OWNER TO postgres;

--
-- Name: productImage_productImageId_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public."productImage_productImageId_seq" OWNED BY public."productImage"."productImageId";


--
-- Name: product_productId_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public."product_productId_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public."product_productId_seq" OWNER TO postgres;

--
-- Name: product_productId_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public."product_productId_seq" OWNED BY public.product."productId";


--
-- Name: review; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.review (
    "reviewId" bigint NOT NULL,
    "productId" bigint NOT NULL,
    "userId" bigint NOT NULL,
    rating integer NOT NULL,
    "reviewText" text,
    "createdAt" timestamp with time zone DEFAULT now() NOT NULL,
    "updatedAt" timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT review_rating_check CHECK (((rating >= 1) AND (rating <= 5)))
);


ALTER TABLE public.review OWNER TO postgres;

--
-- Name: review_reviewId_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public."review_reviewId_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public."review_reviewId_seq" OWNER TO postgres;

--
-- Name: review_reviewId_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public."review_reviewId_seq" OWNED BY public.review."reviewId";


--
-- Name: role; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.role (
    "roleId" integer NOT NULL,
    "roleName" character varying(100) NOT NULL
);


ALTER TABLE public.role OWNER TO postgres;

--
-- Name: role_roleId_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public."role_roleId_seq"
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public."role_roleId_seq" OWNER TO postgres;

--
-- Name: role_roleId_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public."role_roleId_seq" OWNED BY public.role."roleId";


--
-- Name: user; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public."user" (
    "userId" bigint NOT NULL,
    password character varying(100) NOT NULL,
    last_login timestamp with time zone,
    is_superuser boolean DEFAULT false NOT NULL,
    username character varying(150) NOT NULL,
    first_name character varying(150) DEFAULT ''::character varying NOT NULL,
    last_name character varying(150) DEFAULT ''::character varying NOT NULL,
    email character varying(255) NOT NULL,
    is_staff boolean DEFAULT false NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    date_joined timestamp with time zone DEFAULT now() NOT NULL,
    "lastName" character varying(100) NOT NULL,
    "firstName" character varying(100) NOT NULL,
    "middleName" character varying(100),
    "roleId" integer NOT NULL,
    phone character varying(11) NOT NULL,
    "birthDate" date NOT NULL,
    "createdAt" timestamp with time zone DEFAULT now() NOT NULL,
    CONSTRAINT user_phone_check CHECK (((phone)::text ~ '^[0-9]{11}$'::text))
);


ALTER TABLE public."user" OWNER TO postgres;

--
-- Name: user_groups; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_groups (
    id bigint NOT NULL,
    user_id bigint NOT NULL,
    group_id integer NOT NULL
);


ALTER TABLE public.user_groups OWNER TO postgres;

--
-- Name: user_groups_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.user_groups_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.user_groups_id_seq OWNER TO postgres;

--
-- Name: user_groups_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.user_groups_id_seq OWNED BY public.user_groups.id;


--
-- Name: user_userId_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public."user_userId_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public."user_userId_seq" OWNER TO postgres;

--
-- Name: user_userId_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public."user_userId_seq" OWNED BY public."user"."userId";


--
-- Name: user_user_permissions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_user_permissions (
    id bigint NOT NULL,
    user_id bigint NOT NULL,
    permission_id integer NOT NULL
);


ALTER TABLE public.user_user_permissions OWNER TO postgres;

--
-- Name: user_user_permissions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.user_user_permissions_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.user_user_permissions_id_seq OWNER TO postgres;

--
-- Name: user_user_permissions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.user_user_permissions_id_seq OWNED BY public.user_user_permissions.id;


--
-- Name: v_order_details; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.v_order_details AS
 SELECT o."orderId",
    (((u."firstName")::text || ' '::text) || (u."lastName")::text) AS "customerName",
    u.email AS "customerEmail",
    os."orderStatusName" AS status,
    o."deliveryType",
    o."paymentType",
    o."paymentStatus",
    o.total,
    o."createdAt" AS "orderDate",
    oi."orderItemId",
    p."productName",
    oi.quantity,
    oi."unitPrice",
    ((oi.quantity)::numeric * oi."unitPrice") AS "lineTotal"
   FROM ((((public."order" o
     JOIN public."user" u ON ((o."userId" = u."userId")))
     JOIN public."orderStatus" os ON ((o."orderStatusId" = os."orderStatusId")))
     JOIN public."orderItem" oi ON ((o."orderId" = oi."orderId")))
     JOIN public.product p ON ((oi."productId" = p."productId")));


ALTER VIEW public.v_order_details OWNER TO postgres;

--
-- Name: v_popular_products; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.v_popular_products AS
 SELECT p."productId",
    p."productName",
    c."categoryName",
    sum(oi.quantity) AS "totalSold",
    sum(((oi.quantity)::numeric * oi."unitPrice")) AS "totalRevenue",
    COALESCE(round(avg(r.rating), 2), (0)::numeric) AS "avgRating"
   FROM (((((public.product p
     JOIN public.category c ON ((p."categoryId" = c."categoryId")))
     JOIN public."orderItem" oi ON ((p."productId" = oi."productId")))
     JOIN public."order" o ON ((oi."orderId" = o."orderId")))
     JOIN public."orderStatus" os ON ((o."orderStatusId" = os."orderStatusId")))
     LEFT JOIN public.review r ON ((p."productId" = r."productId")))
  WHERE ((os."orderStatusName")::text <> 'Отменен'::text)
  GROUP BY p."productId", p."productName", c."categoryName"
  ORDER BY (sum(oi.quantity)) DESC;


ALTER VIEW public.v_popular_products OWNER TO postgres;

--
-- Name: v_product_catalog; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.v_product_catalog AS
 SELECT p."productId",
    p."productName",
    p.price,
    p.quantity AS "stockQuantity",
    p."ageRating",
    c."categoryName",
    b."brandName",
    b."brandCountry",
    COALESCE(round(avg(r.rating), 2), (0)::numeric) AS "avgRating",
    count(r."reviewId") AS "reviewCount"
   FROM (((public.product p
     JOIN public.category c ON ((p."categoryId" = c."categoryId")))
     JOIN public.brand b ON ((p."brandId" = b."brandId")))
     LEFT JOIN public.review r ON ((p."productId" = r."productId")))
  GROUP BY p."productId", p."productName", p.price, p.quantity, p."ageRating", c."categoryName", b."brandName", b."brandCountry";


ALTER VIEW public.v_product_catalog OWNER TO postgres;

--
-- Name: v_sales_report; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.v_sales_report AS
 SELECT (date_trunc('month'::text, o."createdAt"))::date AS month,
    count(DISTINCT o."orderId") AS "orderCount",
    sum(o.total) AS revenue,
    round(avg(o.total), 2) AS "avgOrderTotal"
   FROM (public."order" o
     JOIN public."orderStatus" os ON ((o."orderStatusId" = os."orderStatusId")))
  WHERE ((os."orderStatusName")::text <> 'Отменен'::text)
  GROUP BY (date_trunc('month'::text, o."createdAt"))
  ORDER BY ((date_trunc('month'::text, o."createdAt"))::date) DESC;


ALTER VIEW public.v_sales_report OWNER TO postgres;

--
-- Name: v_user_activity; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.v_user_activity AS
 SELECT u."userId",
    (((u."firstName")::text || ' '::text) || (u."lastName")::text) AS "fullName",
    u.email,
    r."roleName",
    count(DISTINCT o."orderId") AS "orderCount",
    COALESCE(sum(o.total), (0)::numeric) AS "totalSpent",
    count(DISTINCT rev."reviewId") AS "reviewCount",
    u."createdAt" AS "registeredAt"
   FROM (((public."user" u
     JOIN public.role r ON ((u."roleId" = r."roleId")))
     LEFT JOIN public."order" o ON ((u."userId" = o."userId")))
     LEFT JOIN public.review rev ON ((u."userId" = rev."userId")))
  GROUP BY u."userId", u."firstName", u."lastName", u.email, r."roleName", u."createdAt";


ALTER VIEW public.v_user_activity OWNER TO postgres;

--
-- Name: wishlist; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.wishlist (
    "wishlistId" bigint NOT NULL,
    "userId" bigint NOT NULL,
    "productId" bigint NOT NULL
);


ALTER TABLE public.wishlist OWNER TO postgres;

--
-- Name: wishlist_wishlistId_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public."wishlist_wishlistId_seq"
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public."wishlist_wishlistId_seq" OWNER TO postgres;

--
-- Name: wishlist_wishlistId_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public."wishlist_wishlistId_seq" OWNED BY public.wishlist."wishlistId";


--
-- Name: address addressId; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.address ALTER COLUMN "addressId" SET DEFAULT nextval('public."address_addressId_seq"'::regclass);


--
-- Name: auditLog auditLogId; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."auditLog" ALTER COLUMN "auditLogId" SET DEFAULT nextval('public."auditLog_auditLogId_seq"'::regclass);


--
-- Name: brand brandId; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.brand ALTER COLUMN "brandId" SET DEFAULT nextval('public."brand_brandId_seq"'::regclass);


--
-- Name: cart cartId; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.cart ALTER COLUMN "cartId" SET DEFAULT nextval('public."cart_cartId_seq"'::regclass);


--
-- Name: category categoryId; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.category ALTER COLUMN "categoryId" SET DEFAULT nextval('public."category_categoryId_seq"'::regclass);


--
-- Name: order orderId; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."order" ALTER COLUMN "orderId" SET DEFAULT nextval('public."order_orderId_seq"'::regclass);


--
-- Name: orderItem orderItemId; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."orderItem" ALTER COLUMN "orderItemId" SET DEFAULT nextval('public."orderItem_orderItemId_seq"'::regclass);


--
-- Name: orderStatus orderStatusId; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."orderStatus" ALTER COLUMN "orderStatusId" SET DEFAULT nextval('public."orderStatus_orderStatusId_seq"'::regclass);


--
-- Name: parentChild parentChildId; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."parentChild" ALTER COLUMN "parentChildId" SET DEFAULT nextval('public."parentChild_parentChildId_seq"'::regclass);


--
-- Name: product productId; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.product ALTER COLUMN "productId" SET DEFAULT nextval('public."product_productId_seq"'::regclass);


--
-- Name: productAttribute productAttributeId; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."productAttribute" ALTER COLUMN "productAttributeId" SET DEFAULT nextval('public."productAttribute_productAttributeId_seq"'::regclass);


--
-- Name: productImage productImageId; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."productImage" ALTER COLUMN "productImageId" SET DEFAULT nextval('public."productImage_productImageId_seq"'::regclass);


--
-- Name: review reviewId; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.review ALTER COLUMN "reviewId" SET DEFAULT nextval('public."review_reviewId_seq"'::regclass);


--
-- Name: role roleId; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.role ALTER COLUMN "roleId" SET DEFAULT nextval('public."role_roleId_seq"'::regclass);


--
-- Name: user userId; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."user" ALTER COLUMN "userId" SET DEFAULT nextval('public."user_userId_seq"'::regclass);


--
-- Name: user_groups id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_groups ALTER COLUMN id SET DEFAULT nextval('public.user_groups_id_seq'::regclass);


--
-- Name: user_user_permissions id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_user_permissions ALTER COLUMN id SET DEFAULT nextval('public.user_user_permissions_id_seq'::regclass);


--
-- Name: wishlist wishlistId; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wishlist ALTER COLUMN "wishlistId" SET DEFAULT nextval('public."wishlist_wishlistId_seq"'::regclass);


--
-- Data for Name: address; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.address ("addressId", "userId", city, street, house, flat, index) FROM stdin;
1	2	Москва	ул. Ленина	12а	12	121212
\.


--
-- Data for Name: auditLog; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public."auditLog" ("auditLogId", "userId", action, "tableName", "recordId", "oldValues", "newValues", "createdAt") FROM stdin;
1	2	CREATE	category	1	\N	{"categoryId": 1, "categoryName": "Куклы", "categoryDescription": "Куклы — больше, чем просто игрушки. Это инструмент для развития эмоционального интеллекта, воображения и социальных навыков. В нашей коллекции вы найдёте кукол разных профессий, культур и стилей, которые помогут ребёнку познавать мир через игру."}	2026-02-07 19:44:50.484663+03
2	2	CREATE	category	2	\N	{"categoryId": 2, "categoryName": "Конструкторы", "categoryDescription": "Конструкторы — безграничный мир для фантазии и инженерии. От первых крупных деталей для малышей до сложных технических моделей. Собирайте, творите, ломайте и создавайте снова! Это лучший тренажер для ума, мелкой моторики и пространственного мышления."}	2026-02-07 19:45:31.297894+03
3	2	CREATE	category	3	\N	{"categoryId": 3, "categoryName": "Мягкие игрушки", "categoryDescription": "Мягкие игрушки — первые друзья, самые верные слушатели секретов и незаменимые спутники в объятиях перед сном. Пушистые мишки, зайчата, фантастические зверушки — каждый из них готов дарить тепло, утешение и стать героем любой детской игры."}	2026-02-07 19:46:58.893087+03
4	2	CREATE	category	4	\N	{"categoryId": 4, "categoryName": "Машинки", "categoryDescription": "Машинки. Врум-врум! Гоночные болиды, мощные грузовики, полицейские и пожарные машины — соберите свой автопарк и создайте мегаполис на полу детской комнаты!"}	2026-02-07 19:47:29.017652+03
5	2	CREATE	brand	1	\N	{"brandId": 1, "brandName": "Barbie (Mattel)", "brandCountry": "США", "brandDescription": "Культовый мировой бренд, создающий эталон модной куклы. Barbie — это не просто игрушка, а героиня с историей, множеством профессий и безграничными возможностями для сюжетной игры. Бренд фокусируется на идее «Ты можешь быть кем угодно», предлагая огромный выбор кукол, наборов, домиков и аксессуаров."}	2026-02-07 19:48:44.053+03
6	2	CREATE	brand	2	\N	{"brandId": 2, "brandName": "L.O.L. Surprise! (MGA Entertainment)", "brandCountry": "США", "brandDescription": "Один из самых популярных современных брендов, построенный на концепции «сюрприза». Куклы и аксессуары продаются в многослойных шариках-сюрпризах, которые нужно распаковывать, что создает азарт и элемент коллекционирования. Бренд отличается ярким, дерзким стилем и обширной вселенной персонажей."}	2026-02-07 19:49:01.615492+03
7	2	CREATE	brand	3	\N	{"brandId": 3, "brandName": "LEGO", "brandCountry": "Дания", "brandDescription": "Мировой лидер и законодатель мод в индустрии конструкторов. LEGO славится безупречным качеством пластика, точностью деталей и безграничными возможностями для творчества. Бренд объединяет классические наборы с лицензированными сериями по мотивам популярных фильмов и игр (Star Wars, Harry Potter, Marvel), а также продвинутые технические (Technic) и образовательные (Education) линии."}	2026-02-07 19:49:24.07781+03
8	2	CREATE	brand	4	\N	{"brandId": 4, "brandName": "MAGFORMERS", "brandCountry": "США", "brandDescription": "Инновационный бренд магнитных конструкторов. Его фишка — встроенные в края деталей неодимовые магниты, которые всегда притягиваются, что позволяет легко и быстро создавать 2D и 3D фигуры. MAGFORMERS считается образовательным конструктором, идеально подходящим для изучения основ геометрии, магнетизма и развития пространственного мышления."}	2026-02-07 19:49:52.679761+03
9	2	CREATE	brand	5	\N	{"brandId": 5, "brandName": "GUND", "brandCountry": "США", "brandDescription": "Легендарный американский бренд, существующий более 120 лет. GUND — синоним высочайшего качества, безопасности и невероятной мягкости материалов. Их игрушки часто становятся «первым другом» ребенка и передаются по наследству. Бренд известен своими классическими мишками Тедди и персонажами по лицензии Disney."}	2026-02-07 19:50:15.15907+03
10	2	CREATE	brand	6	\N	{"brandId": 6, "brandName": "Aurora World", "brandCountry": "Южная Корея", "brandDescription": "Крупный мировой производитель, предлагающий огромный ассортимент плюшевых игрушек по доступным ценам. Отличительные черты — яркий дизайн, большие глаза у зверушек (технология «большие глазки» — YooHoo) и разнообразие: от классических мишек до тематических серий, игрушек-антистресс и гигантских плюшевых животных."}	2026-02-07 19:50:39.920636+03
11	2	CREATE	brand	7	\N	{"brandId": 7, "brandName": "Hot Wheels (Mattel)", "brandCountry": "США", "brandDescription": "Самый узнаваемый в мире бренд миниатюрных машинок масштаба 1:64. Легендарные гоночные и тюнингованные автомобили с уникальным дизайном, фантастической детализацией и культовой оранжевой трековой системой. Бренд построен на философии скорости, адреналина и невероятных трюков, а также активно развивает направление коллекционирования."}	2026-02-07 19:51:02.244415+03
12	2	CREATE	brand	8	\N	{"brandId": 8, "brandName": "Bruder", "brandCountry": "Германия", "brandDescription": "Ведущий мировой производитель реалистичных моделей спецтехники и коммерческих автомобилей в крупном масштабе (обычно 1:16). Игрушки Bruder — это высочайшая детализация, прочность, функциональность (открываются двери, поднимается кузов) и лицензионное сходство с реальными машинами MAN, Mercedes-Benz и др. Идеальны для реалистичной сюжетно-ролевой игры."}	2026-02-07 19:51:25.371107+03
13	2	CREATE	product	1	\N	{"price": 1699.0, "brandId": 1, "quantity": 21, "weightKg": 0.33, "ageRating": 3, "productId": 1, "categoryId": 1, "dimensions": "6,5x16,5x32,5", "productName": "Кукла модельная Barbie Made to move Йога", "productDescription": "Барби регулярно тренируется, развивая свою гибкость. Для занятий и медитаций она надевает удобный эластичный костюм: топ и леггинсы в розово-сиреневых тонах в стиле тай-дай. Свои вьющиеся каштановые волосы Барби собирает в хвост, чтобы ей ничего не мешало. Кукла станет хорошим подарком для девочки, которая увлекается фитнесом и йогой.\\n\\n22 подвижных сустава — кукла может принимать множество реалистичных поз.\\nКукла не может стоять самостоятельно."}	2026-02-07 19:54:59.893709+03
14	2	CREATE	productAttribute	1	\N	{"productId": 1, "productAttributeId": 1, "productAttributeName": "Тип куклы", "productAttributeUnit": null, "productAttributeValue": "модельная"}	2026-02-07 19:55:00.182676+03
15	2	CREATE	productAttribute	2	\N	{"productId": 1, "productAttributeId": 2, "productAttributeName": "Материал", "productAttributeUnit": null, "productAttributeValue": "пластик, текстиль"}	2026-02-07 19:55:00.248284+03
16	2	CREATE	productImage	1	\N	{"url": "/media/products/4a19375286434a749af8c6ebdb4cb524.webp", "isMain": true, "altText": "T5E2gZWkO1pNyrqWBjv9f0cn6QT4ORjcQftwsaBOFt4=.webp", "productId": 1, "productImageId": 1}	2026-02-07 19:55:00.381943+03
17	2	CREATE	productImage	2	\N	{"url": "/media/products/86456cd8e5d946bab76203bbf2573a55.webp", "isMain": false, "altText": "24OjFhNIp2gZNxhpba5zQ-u_UECR4V1OyDkd2XrsOF8=.webp", "productId": 1, "productImageId": 2}	2026-02-07 19:55:00.499183+03
18	2	UPDATE	order	1	{"note": "", "total": 3398.0, "userId": 2, "orderId": 1, "addressId": 1, "createdAt": "2026-02-07T16:56:55.366104+00:00", "paymentType": "онлайн", "deliveryType": "курьером", "orderStatusId": 1, "paymentStatus": "оплачено"}	{"note": "", "total": 3398.0, "userId": 2, "orderId": 1, "addressId": 1, "createdAt": "2026-02-07T16:56:55.366104+00:00", "paymentType": "онлайн", "deliveryType": "курьером", "orderStatusId": 4, "paymentStatus": "оплачено"}	2026-02-07 19:57:38.037508+03
19	2	CREATE	category	5	\N	{"categoryId": 5, "categoryName": "Кукла", "categoryDescription": "Куклы — больше, чем просто игрушки. Это инструмент для развития эмоционального интеллекта, воображения и социальных навыков. В нашей коллекции вы найдёте кукол разных профессий, культур и стилей, которые помогут ребёнку познавать мир через игру."}	2026-02-07 20:10:52.049925+03
20	2	CREATE	category	6	\N	{"categoryId": 6, "categoryName": "Куколка", "categoryDescription": "Куклы — больше, чем просто игрушки. Это инструмент для развития эмоционального интеллекта, воображения и социальных навыков. В нашей коллекции вы найдёте кукол разных профессий, культур и стилей, которые помогут ребёнку познавать мир через игру."}	2026-02-07 20:11:17.291313+03
21	2	DELETE	category	6	{"categoryId": 6, "categoryName": "Куколка", "categoryDescription": "Куклы — больше, чем просто игрушки. Это инструмент для развития эмоционального интеллекта, воображения и социальных навыков. В нашей коллекции вы найдёте кукол разных профессий, культур и стилей, которые помогут ребёнку познавать мир через игру."}	\N	2026-02-07 20:11:21.199368+03
22	2	DELETE	category	5	{"categoryId": 5, "categoryName": "Кукла", "categoryDescription": "Куклы — больше, чем просто игрушки. Это инструмент для развития эмоционального интеллекта, воображения и социальных навыков. В нашей коллекции вы найдёте кукол разных профессий, культур и стилей, которые помогут ребёнку познавать мир через игру."}	\N	2026-02-07 20:11:24.511597+03
23	2	UPDATE	brand	8	{"brandId": 8, "brandName": "Bruder", "brandCountry": "Германия", "brandDescription": "Ведущий мировой производитель реалистичных моделей спецтехники и коммерческих автомобилей в крупном масштабе (обычно 1:16). Игрушки Bruder — это высочайшая детализация, прочность, функциональность (открываются двери, поднимается кузов) и лицензионное сходство с реальными машинами MAN, Mercedes-Benz и др. Идеальны для реалистичной сюжетно-ролевой игры."}	{"brandId": 8, "brandName": "Bruderу", "brandCountry": "Германия", "brandDescription": "Ведущий мировой производитель реалистичных моделей спецтехники и коммерческих автомобилей в крупном масштабе (обычно 1:16). Игрушки Bruder — это высочайшая детализация, прочность, функциональность (открываются двери, поднимается кузов) и лицензионное сходство с реальными машинами MAN, Mercedes-Benz и др. Идеальны для реалистичной сюжетно-ролевой игры."}	2026-02-07 20:11:45.083029+03
24	2	UPDATE	brand	8	{"brandId": 8, "brandName": "Bruderу", "brandCountry": "Германия", "brandDescription": "Ведущий мировой производитель реалистичных моделей спецтехники и коммерческих автомобилей в крупном масштабе (обычно 1:16). Игрушки Bruder — это высочайшая детализация, прочность, функциональность (открываются двери, поднимается кузов) и лицензионное сходство с реальными машинами MAN, Mercedes-Benz и др. Идеальны для реалистичной сюжетно-ролевой игры."}	{"brandId": 8, "brandName": "Bruder", "brandCountry": "Германия", "brandDescription": "Ведущий мировой производитель реалистичных моделей спецтехники и коммерческих автомобилей в крупном масштабе (обычно 1:16). Игрушки Bruder — это высочайшая детализация, прочность, функциональность (открываются двери, поднимается кузов) и лицензионное сходство с реальными машинами MAN, Mercedes-Benz и др. Идеальны для реалистичной сюжетно-ролевой игры."}	2026-02-07 20:11:52.770388+03
25	2	UPDATE	user	2	{"email": "ivanov_joybox@mail.ru", "phone": "89089089898", "roleId": 4, "userId": 2, "is_staff": false, "lastName": "Lupa", "password": "pbkdf2_sha256$1000000$AIBIljEbIFIsfd4bwaNhDX$9TMGvm2GZsw66VE1MY2iuUJjrWUsvqDsLBAeGZHdMaE=", "username": "ivanov_joybox@mail.ru", "birthDate": "2006-10-12", "createdAt": "2026-02-07T16:39:32.828638+00:00", "firstName": "Pupa", "is_active": true, "last_name": "", "first_name": "", "last_login": null, "middleName": "Manager", "date_joined": "2026-02-07T16:39:32.828677+00:00", "is_superuser": false}	{"email": "ivanov_joybox@mail.ru", "phone": "89089089890", "roleId": 4, "userId": 2, "is_staff": false, "lastName": "Lupa", "password": "pbkdf2_sha256$1000000$AIBIljEbIFIsfd4bwaNhDX$9TMGvm2GZsw66VE1MY2iuUJjrWUsvqDsLBAeGZHdMaE=", "username": "ivanov_joybox@mail.ru", "birthDate": "2006-10-12", "createdAt": "2026-02-07T16:39:32.828638+00:00", "firstName": "Pupa", "is_active": true, "last_name": "", "first_name": "", "last_login": null, "middleName": "Manager", "date_joined": "2026-02-07T16:39:32.828677+00:00", "is_superuser": false}	2026-02-07 20:12:10.851234+03
26	2	UPDATE	user	2	{"email": "ivanov_joybox@mail.ru", "phone": "89089089898", "roleId": 4, "userId": 2, "is_staff": false, "lastName": "Lupa", "username": "ivanov_joybox@mail.ru", "birthDate": "2006-10-12", "createdAt": "2026-02-07T16:39:32.828638+00:00", "firstName": "Pupa", "is_active": true, "last_name": "", "first_name": "", "last_login": null, "middleName": "Manager", "date_joined": "2026-02-07T16:39:32.828677+00:00", "is_superuser": false}	{"email": "ivanov_joybox@mail.ru", "phone": "89089089890", "roleId": 4, "userId": 2, "is_staff": false, "lastName": "Lupa", "username": "ivanov_joybox@mail.ru", "birthDate": "2006-10-12", "createdAt": "2026-02-07T16:39:32.828638+00:00", "firstName": "Pupa", "is_active": true, "last_name": "", "first_name": "", "last_login": null, "middleName": "Manager", "date_joined": "2026-02-07T16:39:32.828677+00:00", "is_superuser": false}	2026-02-07 20:12:10.884747+03
27	2	UPDATE	user	2	{"email": "ivanov_joybox@mail.ru", "phone": "89089089890", "roleId": 4, "userId": 2, "is_staff": false, "lastName": "Lupa", "password": "pbkdf2_sha256$1000000$AIBIljEbIFIsfd4bwaNhDX$9TMGvm2GZsw66VE1MY2iuUJjrWUsvqDsLBAeGZHdMaE=", "username": "ivanov_joybox@mail.ru", "birthDate": "2006-10-12", "createdAt": "2026-02-07T16:39:32.828638+00:00", "firstName": "Pupa", "is_active": true, "last_name": "", "first_name": "", "last_login": null, "middleName": "Manager", "date_joined": "2026-02-07T16:39:32.828677+00:00", "is_superuser": false}	{"email": "ivanov_joybox@mail.ru", "phone": "89089089890", "roleId": 4, "userId": 2, "is_staff": false, "lastName": "Lupa", "password": "pbkdf2_sha256$1000000$AIBIljEbIFIsfd4bwaNhDX$9TMGvm2GZsw66VE1MY2iuUJjrWUsvqDsLBAeGZHdMaE=", "username": "ivanov_joybox@mail.ru", "birthDate": "2006-10-12", "createdAt": "2026-02-07T16:39:32.828638+00:00", "firstName": "Pupa", "is_active": true, "last_name": "", "first_name": "", "last_login": null, "middleName": "Manager", "date_joined": "2026-02-07T16:39:32.828677+00:00", "is_superuser": false}	2026-02-07 20:12:22.62881+03
28	2	UPDATE	user	2	{"email": "ivanov_joybox@mail.ru", "phone": "89089089890", "roleId": 4, "userId": 2, "is_staff": false, "lastName": "Lupa", "username": "ivanov_joybox@mail.ru", "birthDate": "2006-10-12", "createdAt": "2026-02-07T16:39:32.828638+00:00", "firstName": "Pupa", "is_active": true, "last_name": "", "first_name": "", "last_login": null, "middleName": "Manager", "date_joined": "2026-02-07T16:39:32.828677+00:00", "is_superuser": false}	{"email": "ivanov_joybox@mail.ru", "phone": "89089089890", "roleId": 4, "userId": 2, "is_staff": false, "lastName": "Lupa", "username": "ivanov_joybox@mail.ru", "birthDate": "2006-10-12", "createdAt": "2026-02-07T16:39:32.828638+00:00", "firstName": "Pupa", "is_active": true, "last_name": "", "first_name": "", "last_login": null, "middleName": "Manager", "date_joined": "2026-02-07T16:39:32.828677+00:00", "is_superuser": false}	2026-02-07 20:12:22.633833+03
29	2	UPDATE	order	1	{"note": "", "total": 3398.00, "userId": 2, "orderId": 1, "addressId": 1, "createdAt": "2026-02-07T16:56:55.366104+00:00", "paymentType": "онлайн", "deliveryType": "курьером", "orderStatusId": 4, "paymentStatus": "оплачено"}	{"note": "", "total": 3398.00, "userId": 2, "orderId": 1, "addressId": 1, "createdAt": "2026-02-07T16:56:55.366104+00:00", "paymentType": "онлайн", "deliveryType": "курьером", "orderStatusId": 3, "paymentStatus": "оплачено"}	2026-02-07 20:12:32.077758+03
30	2	UPDATE	order	1	{"note": "", "total": 3398.0, "userId": 2, "orderId": 1, "addressId": 1, "createdAt": "2026-02-07T16:56:55.366104+00:00", "paymentType": "онлайн", "deliveryType": "курьером", "orderStatusId": 4, "paymentStatus": "оплачено"}	{"note": "", "total": 3398.0, "userId": 2, "orderId": 1, "addressId": 1, "createdAt": "2026-02-07T16:56:55.366104+00:00", "paymentType": "онлайн", "deliveryType": "курьером", "orderStatusId": 3, "paymentStatus": "оплачено"}	2026-02-07 20:12:32.116523+03
31	2	UPDATE	order	1	{"note": "", "total": 3398.00, "userId": 2, "orderId": 1, "addressId": 1, "createdAt": "2026-02-07T16:56:55.366104+00:00", "paymentType": "онлайн", "deliveryType": "курьером", "orderStatusId": 3, "paymentStatus": "оплачено"}	{"note": "", "total": 3398.00, "userId": 2, "orderId": 1, "addressId": 1, "createdAt": "2026-02-07T16:56:55.366104+00:00", "paymentType": "онлайн", "deliveryType": "курьером", "orderStatusId": 4, "paymentStatus": "оплачено"}	2026-02-07 20:12:36.999169+03
32	2	UPDATE	order	1	{"note": "", "total": 3398.0, "userId": 2, "orderId": 1, "addressId": 1, "createdAt": "2026-02-07T16:56:55.366104+00:00", "paymentType": "онлайн", "deliveryType": "курьером", "orderStatusId": 3, "paymentStatus": "оплачено"}	{"note": "", "total": 3398.0, "userId": 2, "orderId": 1, "addressId": 1, "createdAt": "2026-02-07T16:56:55.366104+00:00", "paymentType": "онлайн", "deliveryType": "курьером", "orderStatusId": 4, "paymentStatus": "оплачено"}	2026-02-07 20:12:37.011998+03
37	2	CREATE	category	7	\N	{"categoryId": 7, "categoryName": "Кукла", "categoryDescription": "ццццц"}	2026-02-07 20:13:47.935238+03
38	2	DELETE	category	7	{"categoryId": 7, "categoryName": "Кукла", "categoryDescription": "ццццц"}	\N	2026-02-07 20:13:51.923034+03
39	2	CREATE	brand	9	\N	{"brandId": 9, "brandName": "Bruderс", "brandCountry": "США", "brandDescription": "сч"}	2026-02-07 20:14:02.648696+03
40	2	DELETE	brand	9	{"brandId": 9, "brandName": "Bruderс", "brandCountry": "США", "brandDescription": "сч"}	\N	2026-02-07 20:14:06.730385+03
42	2	CREATE	category	8	\N	{"categoryId": 8, "categoryName": "Кукл", "categoryDescription": "Куклы — больше, чем просто игрушки. Это инструмент для развития эмоционального интеллекта, воображения и социальных навыков. В нашей коллекции вы найдёте кукол разных профессий, культур и стилей, которые помогут ребёнку познавать мир через игру."}	2026-02-07 20:27:04.083498+03
43	2	DELETE	category	8	{"categoryId": 8, "categoryName": "Кукл", "categoryDescription": "Куклы — больше, чем просто игрушки. Это инструмент для развития эмоционального интеллекта, воображения и социальных навыков. В нашей коллекции вы найдёте кукол разных профессий, культур и стилей, которые помогут ребёнку познавать мир через игру."}	\N	2026-02-07 20:27:09.078119+03
44	2	CREATE	product	3	\N	{"price": 11.00, "brandId": 1, "quantity": 11, "weightKg": 1.00, "ageRating": 16, "productId": 3, "categoryId": 2, "dimensions": "15x10x5", "productName": "Barbie Doll Mermaid Barbie", "productDescription": "вв"}	2026-02-07 20:27:29.119912+03
45	2	CREATE	productImage	3	\N	{"url": "/media/products/fa6d006e21634321ab4b219749c39094.png", "isMain": true, "altText": "NBPihOBpYaxhGACX.png", "productId": 3, "productImageId": 3}	2026-02-07 20:27:29.339946+03
46	2	UPDATE	product	3	{"price": 11.00, "brandId": 1, "quantity": 11, "weightKg": 1.00, "ageRating": 16, "productId": 3, "categoryId": 2, "dimensions": "15x10x5", "productName": "Barbie Doll Mermaid Barbie", "productDescription": "вв"}	{"price": 11.00, "brandId": 1, "quantity": 111, "weightKg": 1.00, "ageRating": 16, "productId": 3, "categoryId": 2, "dimensions": "15x10x5", "productName": "Barbie Doll Mermaid Barbie", "productDescription": "вв"}	2026-02-07 20:27:41.853328+03
47	2	UPDATE	product	1	{"price": 1699.00, "brandId": 1, "quantity": 19, "weightKg": 0.33, "ageRating": 3, "productId": 1, "categoryId": 1, "dimensions": "6,5x16,5x32,5", "productName": "Кукла модельная Barbie Made to move Йога", "productDescription": "Барби регулярно тренируется, развивая свою гибкость. Для занятий и медитаций она надевает удобный эластичный костюм: топ и леггинсы в розово-сиреневых тонах в стиле тай-дай. Свои вьющиеся каштановые волосы Барби собирает в хвост, чтобы ей ничего не мешало. Кукла станет хорошим подарком для девочки, которая увлекается фитнесом и йогой.\\n\\n22 подвижных сустава — кукла может принимать множество реалистичных поз.\\nКукла не может стоять самостоятельно."}	{"price": 1902.88, "brandId": 1, "quantity": 19, "weightKg": 0.33, "ageRating": 3, "productId": 1, "categoryId": 1, "dimensions": "6,5x16,5x32,5", "productName": "Кукла модельная Barbie Made to move Йога", "productDescription": "Барби регулярно тренируется, развивая свою гибкость. Для занятий и медитаций она надевает удобный эластичный костюм: топ и леггинсы в розово-сиреневых тонах в стиле тай-дай. Свои вьющиеся каштановые волосы Барби собирает в хвост, чтобы ей ничего не мешало. Кукла станет хорошим подарком для девочки, которая увлекается фитнесом и йогой.\\n\\n22 подвижных сустава — кукла может принимать множество реалистичных поз.\\nКукла не может стоять самостоятельно."}	2026-02-07 20:34:16.679175+03
48	2	UPDATE	product	1	{"price": 1902.88, "brandId": 1, "quantity": 19, "weightKg": 0.33, "ageRating": 3, "productId": 1, "categoryId": 1, "dimensions": "6,5x16,5x32,5", "productName": "Кукла модельная Barbie Made to move Йога", "productDescription": "Барби регулярно тренируется, развивая свою гибкость. Для занятий и медитаций она надевает удобный эластичный костюм: топ и леггинсы в розово-сиреневых тонах в стиле тай-дай. Свои вьющиеся каштановые волосы Барби собирает в хвост, чтобы ей ничего не мешало. Кукла станет хорошим подарком для девочки, которая увлекается фитнесом и йогой.\\n\\n22 подвижных сустава — кукла может принимать множество реалистичных поз.\\nКукла не может стоять самостоятельно."}	{"price": 1674.53, "brandId": 1, "quantity": 19, "weightKg": 0.33, "ageRating": 3, "productId": 1, "categoryId": 1, "dimensions": "6,5x16,5x32,5", "productName": "Кукла модельная Barbie Made to move Йога", "productDescription": "Барби регулярно тренируется, развивая свою гибкость. Для занятий и медитаций она надевает удобный эластичный костюм: топ и леггинсы в розово-сиреневых тонах в стиле тай-дай. Свои вьющиеся каштановые волосы Барби собирает в хвост, чтобы ей ничего не мешало. Кукла станет хорошим подарком для девочки, которая увлекается фитнесом и йогой.\\n\\n22 подвижных сустава — кукла может принимать множество реалистичных поз.\\nКукла не может стоять самостоятельно."}	2026-02-07 20:34:27.297019+03
49	2	UPDATE	product	3	{"price": 11.00, "brandId": 1, "quantity": 111, "weightKg": 1.00, "ageRating": 16, "productId": 3, "categoryId": 2, "dimensions": "15x10x5", "productName": "Barbie Doll Mermaid Barbie", "productDescription": "вв"}	{"price": 12.10, "brandId": 1, "quantity": 111, "weightKg": 1.00, "ageRating": 16, "productId": 3, "categoryId": 2, "dimensions": "15x10x5", "productName": "Barbie Doll Mermaid Barbie", "productDescription": "вв"}	2026-02-07 20:35:00.85553+03
50	2	UPDATE	user	2	{"email": "ivanov_joybox@mail.ru", "phone": "89089089890", "roleId": 4, "userId": 2, "is_staff": false, "lastName": "Lupa", "password": "pbkdf2_sha256$1000000$AIBIljEbIFIsfd4bwaNhDX$9TMGvm2GZsw66VE1MY2iuUJjrWUsvqDsLBAeGZHdMaE=", "username": "ivanov_joybox@mail.ru", "birthDate": "2006-10-12", "createdAt": "2026-02-07T19:39:32.828638+03:00", "firstName": "Pupa", "is_active": true, "last_name": "", "first_name": "", "last_login": null, "middleName": "Manager", "date_joined": "2026-02-07T19:39:32.828677+03:00", "is_superuser": false}	{"email": "ivanov_joybox@mail.ru", "phone": "89089089890", "roleId": 2, "userId": 2, "is_staff": false, "lastName": "Lupa", "password": "pbkdf2_sha256$1000000$AIBIljEbIFIsfd4bwaNhDX$9TMGvm2GZsw66VE1MY2iuUJjrWUsvqDsLBAeGZHdMaE=", "username": "ivanov_joybox@mail.ru", "birthDate": "2006-10-12", "createdAt": "2026-02-07T19:39:32.828638+03:00", "firstName": "Pupa", "is_active": true, "last_name": "", "first_name": "", "last_login": null, "middleName": "Manager", "date_joined": "2026-02-07T19:39:32.828677+03:00", "is_superuser": false}	2026-02-07 20:56:52.931947+03
51	2	UPDATE	user	2	{"email": "ivanov_joybox@mail.ru", "phone": "89089089890", "roleId": 2, "userId": 2, "is_staff": false, "lastName": "Lupa", "password": "pbkdf2_sha256$1000000$AIBIljEbIFIsfd4bwaNhDX$9TMGvm2GZsw66VE1MY2iuUJjrWUsvqDsLBAeGZHdMaE=", "username": "ivanov_joybox@mail.ru", "birthDate": "2006-10-12", "createdAt": "2026-02-07T19:39:32.828638+03:00", "firstName": "Pupa", "is_active": true, "last_name": "", "first_name": "", "last_login": null, "middleName": "Manager", "date_joined": "2026-02-07T19:39:32.828677+03:00", "is_superuser": false}	{"email": "ivanov_joybox@mail.ru", "phone": "89089089890", "roleId": 1, "userId": 2, "is_staff": false, "lastName": "Lupa", "password": "pbkdf2_sha256$1000000$AIBIljEbIFIsfd4bwaNhDX$9TMGvm2GZsw66VE1MY2iuUJjrWUsvqDsLBAeGZHdMaE=", "username": "ivanov_joybox@mail.ru", "birthDate": "2006-10-12", "createdAt": "2026-02-07T19:39:32.828638+03:00", "firstName": "Pupa", "is_active": true, "last_name": "", "first_name": "", "last_login": null, "middleName": "Manager", "date_joined": "2026-02-07T19:39:32.828677+03:00", "is_superuser": false}	2026-02-07 20:57:11.711761+03
52	2	UPDATE	user	2	{"email": "ivanov_joybox@mail.ru", "phone": "89089089890", "roleId": 1, "userId": 2, "is_staff": false, "lastName": "Lupa", "password": "pbkdf2_sha256$1000000$AIBIljEbIFIsfd4bwaNhDX$9TMGvm2GZsw66VE1MY2iuUJjrWUsvqDsLBAeGZHdMaE=", "username": "ivanov_joybox@mail.ru", "birthDate": "2006-10-12", "createdAt": "2026-02-07T19:39:32.828638+03:00", "firstName": "Pupa", "is_active": true, "last_name": "", "first_name": "", "last_login": null, "middleName": "Manager", "date_joined": "2026-02-07T19:39:32.828677+03:00", "is_superuser": false}	{"email": "ivanov_joybox@mail.ru", "phone": "89089089890", "roleId": 4, "userId": 2, "is_staff": false, "lastName": "Lupa", "password": "pbkdf2_sha256$1000000$AIBIljEbIFIsfd4bwaNhDX$9TMGvm2GZsw66VE1MY2iuUJjrWUsvqDsLBAeGZHdMaE=", "username": "ivanov_joybox@mail.ru", "birthDate": "2006-10-12", "createdAt": "2026-02-07T19:39:32.828638+03:00", "firstName": "Pupa", "is_active": true, "last_name": "", "first_name": "", "last_login": null, "middleName": "Manager", "date_joined": "2026-02-07T19:39:32.828677+03:00", "is_superuser": false}	2026-02-07 23:16:50.226367+03
53	2	CREATE	backup	0	\N	{"format": "sql", "output": "Создание резервной копии БД «joybox_test»...\\nФормат: sql, Только данные: False\\n\\u001b[32;1mРезервная копия создана: C:\\\\Users\\\\Ast\\\\Desktop\\\\work\\\\JoyBox\\\\joybox\\\\backups\\\\joybox_test_20260207_231929.sql (116.8 КБ)\\u001b[0m\\nC:\\\\Users\\\\Ast\\\\Desktop\\\\work\\\\JoyBox\\\\joybox\\\\backups\\\\joybox_test_20260207_231929.sql", "data_only": false}	2026-02-07 23:19:30.015579+03
54	2	CREATE	backup	0	\N	{"format": "sql", "output": "Создание резервной копии БД «joybox_test»...\\nФормат: sql, Только данные: True\\n\\u001b[32;1mРезервная копия создана: C:\\\\Users\\\\Ast\\\\Desktop\\\\work\\\\JoyBox\\\\joybox\\\\backups\\\\joybox_test_20260207_232309_data.sql (57.2 КБ)\\u001b[0m\\nC:\\\\Users\\\\Ast\\\\Desktop\\\\work\\\\JoyBox\\\\joybox\\\\backups\\\\joybox_test_20260207_232309_data.sql", "data_only": true}	2026-02-07 23:23:09.343686+03
55	2	CREATE	backup	0	\N	{"format": "custom", "output": "Создание резервной копии БД «joybox_test»...\\nФормат: custom, Только данные: True\\n\\u001b[32;1mРезервная копия создана: C:\\\\Users\\\\Ast\\\\Desktop\\\\work\\\\JoyBox\\\\joybox\\\\backups\\\\joybox_test_20260207_232625_data.backup (24.3 КБ)\\u001b[0m\\nC:\\\\Users\\\\Ast\\\\Desktop\\\\work\\\\JoyBox\\\\joybox\\\\backups\\\\joybox_test_20260207_232625_data.backup", "data_only": true}	2026-02-07 23:26:26.237794+03
\.


--
-- Data for Name: auth_group; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.auth_group (id, name) FROM stdin;
\.


--
-- Data for Name: auth_group_permissions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.auth_group_permissions (id, group_id, permission_id) FROM stdin;
\.


--
-- Data for Name: auth_permission; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.auth_permission (id, name, content_type_id, codename) FROM stdin;
1	Can add log entry	1	add_logentry
2	Can change log entry	1	change_logentry
3	Can delete log entry	1	delete_logentry
4	Can view log entry	1	view_logentry
5	Can add permission	2	add_permission
6	Can change permission	2	change_permission
7	Can delete permission	2	delete_permission
8	Can view permission	2	view_permission
9	Can add group	3	add_group
10	Can change group	3	change_group
11	Can delete group	3	delete_group
12	Can view group	3	view_group
13	Can add content type	4	add_contenttype
14	Can change content type	4	change_contenttype
15	Can delete content type	4	delete_contenttype
16	Can view content type	4	view_contenttype
17	Can add session	5	add_session
18	Can change session	5	change_session
19	Can delete session	5	delete_session
20	Can view session	5	view_session
21	Can add Token	6	add_token
22	Can change Token	6	change_token
23	Can delete Token	6	delete_token
24	Can view Token	6	view_token
25	Can add Token	7	add_tokenproxy
26	Can change Token	7	change_tokenproxy
27	Can delete Token	7	delete_tokenproxy
28	Can view Token	7	view_tokenproxy
29	Can add Пользователь	8	add_user
30	Can change Пользователь	8	change_user
31	Can delete Пользователь	8	delete_user
32	Can view Пользователь	8	view_user
33	Can add Адрес	9	add_address
34	Can change Адрес	9	change_address
35	Can delete Адрес	9	delete_address
36	Can view Адрес	9	view_address
37	Can add Журнал аудита	10	add_auditlog
38	Can change Журнал аудита	10	change_auditlog
39	Can delete Журнал аудита	10	delete_auditlog
40	Can view Журнал аудита	10	view_auditlog
41	Can add Бренд	11	add_brand
42	Can change Бренд	11	change_brand
43	Can delete Бренд	11	delete_brand
44	Can view Бренд	11	view_brand
45	Can add Корзина	12	add_cart
46	Can change Корзина	12	change_cart
47	Can delete Корзина	12	delete_cart
48	Can view Корзина	12	view_cart
49	Can add Категория	13	add_category
50	Can change Категория	13	change_category
51	Can delete Категория	13	delete_category
52	Can view Категория	13	view_category
53	Can add Заказ	14	add_order
54	Can change Заказ	14	change_order
55	Can delete Заказ	14	delete_order
56	Can view Заказ	14	view_order
57	Can add Позиция заказа	15	add_orderitem
58	Can change Позиция заказа	15	change_orderitem
59	Can delete Позиция заказа	15	delete_orderitem
60	Can view Позиция заказа	15	view_orderitem
61	Can add Статус заказа	16	add_orderstatus
62	Can change Статус заказа	16	change_orderstatus
63	Can delete Статус заказа	16	delete_orderstatus
64	Can view Статус заказа	16	view_orderstatus
65	Can add Родитель-ребенок	17	add_parentchild
66	Can change Родитель-ребенок	17	change_parentchild
67	Can delete Родитель-ребенок	17	delete_parentchild
68	Can view Родитель-ребенок	17	view_parentchild
69	Can add Продукт	18	add_product
70	Can change Продукт	18	change_product
71	Can delete Продукт	18	delete_product
72	Can view Продукт	18	view_product
73	Can add Атрибут продукта	19	add_productattribute
74	Can change Атрибут продукта	19	change_productattribute
75	Can delete Атрибут продукта	19	delete_productattribute
76	Can view Атрибут продукта	19	view_productattribute
77	Can add Изображение продукта	20	add_productimage
78	Can change Изображение продукта	20	change_productimage
79	Can delete Изображение продукта	20	delete_productimage
80	Can view Изображение продукта	20	view_productimage
81	Can add Отзыв	21	add_review
82	Can change Отзыв	21	change_review
83	Can delete Отзыв	21	delete_review
84	Can view Отзыв	21	view_review
85	Can add Роль	22	add_role
86	Can change Роль	22	change_role
87	Can delete Роль	22	delete_role
88	Can view Роль	22	view_role
89	Can add Список желаний	23	add_wishlist
90	Can change Список желаний	23	change_wishlist
91	Can delete Список желаний	23	delete_wishlist
92	Can view Список желаний	23	view_wishlist
\.


--
-- Data for Name: authtoken_token; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.authtoken_token (key, created, user_id) FROM stdin;
cbaa47991d2767eaa377903ee9902875acdd27ec	2026-02-07 19:42:08.538751+03	2
\.


--
-- Data for Name: brand; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.brand ("brandId", "brandName", "brandDescription", "brandCountry") FROM stdin;
1	Barbie (Mattel)	Культовый мировой бренд, создающий эталон модной куклы. Barbie — это не просто игрушка, а героиня с историей, множеством профессий и безграничными возможностями для сюжетной игры. Бренд фокусируется на идее «Ты можешь быть кем угодно», предлагая огромный выбор кукол, наборов, домиков и аксессуаров.	США
2	L.O.L. Surprise! (MGA Entertainment)	Один из самых популярных современных брендов, построенный на концепции «сюрприза». Куклы и аксессуары продаются в многослойных шариках-сюрпризах, которые нужно распаковывать, что создает азарт и элемент коллекционирования. Бренд отличается ярким, дерзким стилем и обширной вселенной персонажей.	США
3	LEGO	Мировой лидер и законодатель мод в индустрии конструкторов. LEGO славится безупречным качеством пластика, точностью деталей и безграничными возможностями для творчества. Бренд объединяет классические наборы с лицензированными сериями по мотивам популярных фильмов и игр (Star Wars, Harry Potter, Marvel), а также продвинутые технические (Technic) и образовательные (Education) линии.	Дания
4	MAGFORMERS	Инновационный бренд магнитных конструкторов. Его фишка — встроенные в края деталей неодимовые магниты, которые всегда притягиваются, что позволяет легко и быстро создавать 2D и 3D фигуры. MAGFORMERS считается образовательным конструктором, идеально подходящим для изучения основ геометрии, магнетизма и развития пространственного мышления.	США
5	GUND	Легендарный американский бренд, существующий более 120 лет. GUND — синоним высочайшего качества, безопасности и невероятной мягкости материалов. Их игрушки часто становятся «первым другом» ребенка и передаются по наследству. Бренд известен своими классическими мишками Тедди и персонажами по лицензии Disney.	США
6	Aurora World	Крупный мировой производитель, предлагающий огромный ассортимент плюшевых игрушек по доступным ценам. Отличительные черты — яркий дизайн, большие глаза у зверушек (технология «большие глазки» — YooHoo) и разнообразие: от классических мишек до тематических серий, игрушек-антистресс и гигантских плюшевых животных.	Южная Корея
7	Hot Wheels (Mattel)	Самый узнаваемый в мире бренд миниатюрных машинок масштаба 1:64. Легендарные гоночные и тюнингованные автомобили с уникальным дизайном, фантастической детализацией и культовой оранжевой трековой системой. Бренд построен на философии скорости, адреналина и невероятных трюков, а также активно развивает направление коллекционирования.	США
8	Bruder	Ведущий мировой производитель реалистичных моделей спецтехники и коммерческих автомобилей в крупном масштабе (обычно 1:16). Игрушки Bruder — это высочайшая детализация, прочность, функциональность (открываются двери, поднимается кузов) и лицензионное сходство с реальными машинами MAN, Mercedes-Benz и др. Идеальны для реалистичной сюжетно-ролевой игры.	Германия
\.


--
-- Data for Name: cart; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.cart ("cartId", "userId", "productId", quantity) FROM stdin;
\.


--
-- Data for Name: category; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.category ("categoryId", "categoryName", "categoryDescription") FROM stdin;
1	Куклы	Куклы — больше, чем просто игрушки. Это инструмент для развития эмоционального интеллекта, воображения и социальных навыков. В нашей коллекции вы найдёте кукол разных профессий, культур и стилей, которые помогут ребёнку познавать мир через игру.
2	Конструкторы	Конструкторы — безграничный мир для фантазии и инженерии. От первых крупных деталей для малышей до сложных технических моделей. Собирайте, творите, ломайте и создавайте снова! Это лучший тренажер для ума, мелкой моторики и пространственного мышления.
3	Мягкие игрушки	Мягкие игрушки — первые друзья, самые верные слушатели секретов и незаменимые спутники в объятиях перед сном. Пушистые мишки, зайчата, фантастические зверушки — каждый из них готов дарить тепло, утешение и стать героем любой детской игры.
4	Машинки	Машинки. Врум-врум! Гоночные болиды, мощные грузовики, полицейские и пожарные машины — соберите свой автопарк и создайте мегаполис на полу детской комнаты!
\.


--
-- Data for Name: django_admin_log; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.django_admin_log (id, action_time, object_id, object_repr, action_flag, change_message, content_type_id, user_id) FROM stdin;
\.


--
-- Data for Name: django_content_type; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.django_content_type (id, app_label, model) FROM stdin;
1	admin	logentry
2	auth	permission
3	auth	group
4	contenttypes	contenttype
5	sessions	session
6	authtoken	token
7	authtoken	tokenproxy
8	core	user
9	core	address
10	core	auditlog
11	core	brand
12	core	cart
13	core	category
14	core	order
15	core	orderitem
16	core	orderstatus
17	core	parentchild
18	core	product
19	core	productattribute
20	core	productimage
21	core	review
22	core	role
23	core	wishlist
\.


--
-- Data for Name: django_migrations; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.django_migrations (id, app, name, applied) FROM stdin;
1	core	0001_initial	2026-02-07 19:41:33.897895+03
2	contenttypes	0001_initial	2026-02-07 19:41:33.911172+03
3	admin	0001_initial	2026-02-07 19:41:33.946554+03
4	admin	0002_logentry_remove_auto_add	2026-02-07 19:41:33.955882+03
5	admin	0003_logentry_add_action_flag_choices	2026-02-07 19:41:33.9684+03
6	contenttypes	0002_remove_content_type_name	2026-02-07 19:41:33.991566+03
7	auth	0001_initial	2026-02-07 19:41:34.053699+03
8	auth	0002_alter_permission_name_max_length	2026-02-07 19:41:34.059821+03
9	auth	0003_alter_user_email_max_length	2026-02-07 19:41:34.065616+03
10	auth	0004_alter_user_username_opts	2026-02-07 19:41:34.074544+03
11	auth	0005_alter_user_last_login_null	2026-02-07 19:41:34.07869+03
12	auth	0006_require_contenttypes_0002	2026-02-07 19:41:34.080257+03
13	auth	0007_alter_validators_add_error_messages	2026-02-07 19:41:34.083895+03
14	auth	0008_alter_user_username_max_length	2026-02-07 19:41:34.091895+03
15	auth	0009_alter_user_last_name_max_length	2026-02-07 19:41:34.096666+03
16	auth	0010_alter_group_name_max_length	2026-02-07 19:41:34.10792+03
17	auth	0011_update_proxy_permissions	2026-02-07 19:41:34.11565+03
18	auth	0012_alter_user_first_name_max_length	2026-02-07 19:41:34.120276+03
19	authtoken	0001_initial	2026-02-07 19:41:34.137553+03
20	authtoken	0002_auto_20160226_1747	2026-02-07 19:41:34.149245+03
21	authtoken	0003_tokenproxy	2026-02-07 19:41:34.150467+03
22	authtoken	0004_alter_tokenproxy_options	2026-02-07 19:41:34.152797+03
23	sessions	0001_initial	2026-02-07 19:41:34.162146+03
\.


--
-- Data for Name: django_session; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.django_session (session_key, session_data, expire_date) FROM stdin;
\.


--
-- Data for Name: order; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public."order" ("orderId", "userId", "orderStatusId", total, "addressId", "deliveryType", "paymentType", "paymentStatus", note, "createdAt") FROM stdin;
1	2	4	3398.00	1	курьером	онлайн	оплачено		2026-02-07 19:56:55.366104+03
\.


--
-- Data for Name: orderItem; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public."orderItem" ("orderItemId", "orderId", "productId", quantity, "unitPrice") FROM stdin;
1	1	1	2	1699.00
\.


--
-- Data for Name: orderStatus; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public."orderStatus" ("orderStatusId", "orderStatusName") FROM stdin;
1	Новый
2	В обработке
3	Отправлен
4	Доставлен
5	Отменен
\.


--
-- Data for Name: parentChild; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public."parentChild" ("parentChildId", "userId", "childId") FROM stdin;
\.


--
-- Data for Name: product; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.product ("productId", "productName", "productDescription", "categoryId", "brandId", price, "ageRating", quantity, "weightKg", dimensions) FROM stdin;
3	Barbie Doll Mermaid Barbie	вв	2	1	12.10	16	111	1.00	15x10x5
1	Кукла модельная Barbie Made to move Йога	Барби регулярно тренируется, развивая свою гибкость. Для занятий и медитаций она надевает удобный эластичный костюм: топ и леггинсы в розово-сиреневых тонах в стиле тай-дай. Свои вьющиеся каштановые волосы Барби собирает в хвост, чтобы ей ничего не мешало. Кукла станет хорошим подарком для девочки, которая увлекается фитнесом и йогой.\n\n22 подвижных сустава — кукла может принимать множество реалистичных поз.\nКукла не может стоять самостоятельно.	1	1	1674.53	3	19	0.33	6,5x16,5x32,5
\.


--
-- Data for Name: productAttribute; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public."productAttribute" ("productAttributeId", "productId", "productAttributeName", "productAttributeValue", "productAttributeUnit") FROM stdin;
1	1	Тип куклы	модельная	\N
2	1	Материал	пластик, текстиль	\N
\.


--
-- Data for Name: productImage; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public."productImage" ("productImageId", "productId", url, "altText", "isMain") FROM stdin;
1	1	/media/products/4a19375286434a749af8c6ebdb4cb524.webp	T5E2gZWkO1pNyrqWBjv9f0cn6QT4ORjcQftwsaBOFt4=.webp	t
2	1	/media/products/86456cd8e5d946bab76203bbf2573a55.webp	24OjFhNIp2gZNxhpba5zQ-u_UECR4V1OyDkd2XrsOF8=.webp	f
3	3	/media/products/fa6d006e21634321ab4b219749c39094.png	NBPihOBpYaxhGACX.png	t
\.


--
-- Data for Name: review; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.review ("reviewId", "productId", "userId", rating, "reviewText", "createdAt", "updatedAt") FROM stdin;
1	1	2	5	Отличная куколка, дочка очень рада!!!	2026-02-07 19:58:00.706748+03	2026-02-07 19:58:26.370007+03
\.


--
-- Data for Name: role; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.role ("roleId", "roleName") FROM stdin;
1	Покупатель
2	Ребенок
3	Менеджер
4	Администратор
\.


--
-- Data for Name: user; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public."user" ("userId", password, last_login, is_superuser, username, first_name, last_name, email, is_staff, is_active, date_joined, "lastName", "firstName", "middleName", "roleId", phone, "birthDate", "createdAt") FROM stdin;
2	pbkdf2_sha256$1000000$AIBIljEbIFIsfd4bwaNhDX$9TMGvm2GZsw66VE1MY2iuUJjrWUsvqDsLBAeGZHdMaE=	\N	f	ivanov_joybox@mail.ru			ivanov_joybox@mail.ru	f	t	2026-02-07 19:39:32.828677+03	Lupa	Pupa	Manager	4	89089089890	2006-10-12	2026-02-07 19:39:32.828638+03
\.


--
-- Data for Name: user_groups; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.user_groups (id, user_id, group_id) FROM stdin;
\.


--
-- Data for Name: user_user_permissions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.user_user_permissions (id, user_id, permission_id) FROM stdin;
\.


--
-- Data for Name: wishlist; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.wishlist ("wishlistId", "userId", "productId") FROM stdin;
1	2	1
\.


--
-- Name: address_addressId_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public."address_addressId_seq"', 1, true);


--
-- Name: auditLog_auditLogId_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public."auditLog_auditLogId_seq"', 55, true);


--
-- Name: auth_group_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.auth_group_id_seq', 1, false);


--
-- Name: auth_group_permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.auth_group_permissions_id_seq', 1, false);


--
-- Name: auth_permission_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.auth_permission_id_seq', 92, true);


--
-- Name: brand_brandId_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public."brand_brandId_seq"', 9, true);


--
-- Name: cart_cartId_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public."cart_cartId_seq"', 1, true);


--
-- Name: category_categoryId_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public."category_categoryId_seq"', 8, true);


--
-- Name: django_admin_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.django_admin_log_id_seq', 1, false);


--
-- Name: django_content_type_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.django_content_type_id_seq', 23, true);


--
-- Name: django_migrations_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.django_migrations_id_seq', 23, true);


--
-- Name: orderItem_orderItemId_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public."orderItem_orderItemId_seq"', 1, true);


--
-- Name: orderStatus_orderStatusId_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public."orderStatus_orderStatusId_seq"', 5, true);


--
-- Name: order_orderId_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public."order_orderId_seq"', 1, true);


--
-- Name: parentChild_parentChildId_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public."parentChild_parentChildId_seq"', 1, false);


--
-- Name: productAttribute_productAttributeId_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public."productAttribute_productAttributeId_seq"', 2, true);


--
-- Name: productImage_productImageId_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public."productImage_productImageId_seq"', 3, true);


--
-- Name: product_productId_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public."product_productId_seq"', 3, true);


--
-- Name: review_reviewId_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public."review_reviewId_seq"', 1, true);


--
-- Name: role_roleId_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public."role_roleId_seq"', 4, true);


--
-- Name: user_groups_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.user_groups_id_seq', 1, false);


--
-- Name: user_userId_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public."user_userId_seq"', 2, true);


--
-- Name: user_user_permissions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.user_user_permissions_id_seq', 1, false);


--
-- Name: wishlist_wishlistId_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public."wishlist_wishlistId_seq"', 1, true);


--
-- Name: address address_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.address
    ADD CONSTRAINT address_pkey PRIMARY KEY ("addressId");


--
-- Name: auditLog auditLog_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."auditLog"
    ADD CONSTRAINT "auditLog_pkey" PRIMARY KEY ("auditLogId");


--
-- Name: auth_group auth_group_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_group
    ADD CONSTRAINT auth_group_name_key UNIQUE (name);


--
-- Name: auth_group_permissions auth_group_permissions_group_id_permission_id_0cd325b0_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_group_permissions
    ADD CONSTRAINT auth_group_permissions_group_id_permission_id_0cd325b0_uniq UNIQUE (group_id, permission_id);


--
-- Name: auth_group_permissions auth_group_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_group_permissions
    ADD CONSTRAINT auth_group_permissions_pkey PRIMARY KEY (id);


--
-- Name: auth_group auth_group_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_group
    ADD CONSTRAINT auth_group_pkey PRIMARY KEY (id);


--
-- Name: auth_permission auth_permission_content_type_id_codename_01ab375a_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_permission
    ADD CONSTRAINT auth_permission_content_type_id_codename_01ab375a_uniq UNIQUE (content_type_id, codename);


--
-- Name: auth_permission auth_permission_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_permission
    ADD CONSTRAINT auth_permission_pkey PRIMARY KEY (id);


--
-- Name: authtoken_token authtoken_token_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.authtoken_token
    ADD CONSTRAINT authtoken_token_pkey PRIMARY KEY (key);


--
-- Name: authtoken_token authtoken_token_user_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.authtoken_token
    ADD CONSTRAINT authtoken_token_user_id_key UNIQUE (user_id);


--
-- Name: brand brand_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.brand
    ADD CONSTRAINT brand_pkey PRIMARY KEY ("brandId");


--
-- Name: cart cart_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.cart
    ADD CONSTRAINT cart_pkey PRIMARY KEY ("cartId");


--
-- Name: cart cart_user_product_unique; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.cart
    ADD CONSTRAINT cart_user_product_unique UNIQUE ("userId", "productId");


--
-- Name: category category_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.category
    ADD CONSTRAINT category_pkey PRIMARY KEY ("categoryId");


--
-- Name: django_admin_log django_admin_log_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_admin_log
    ADD CONSTRAINT django_admin_log_pkey PRIMARY KEY (id);


--
-- Name: django_content_type django_content_type_app_label_model_76bd3d3b_uniq; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_content_type
    ADD CONSTRAINT django_content_type_app_label_model_76bd3d3b_uniq UNIQUE (app_label, model);


--
-- Name: django_content_type django_content_type_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_content_type
    ADD CONSTRAINT django_content_type_pkey PRIMARY KEY (id);


--
-- Name: django_migrations django_migrations_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_migrations
    ADD CONSTRAINT django_migrations_pkey PRIMARY KEY (id);


--
-- Name: django_session django_session_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_session
    ADD CONSTRAINT django_session_pkey PRIMARY KEY (session_key);


--
-- Name: orderItem orderItem_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."orderItem"
    ADD CONSTRAINT "orderItem_pkey" PRIMARY KEY ("orderItemId");


--
-- Name: orderStatus orderStatus_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."orderStatus"
    ADD CONSTRAINT "orderStatus_pkey" PRIMARY KEY ("orderStatusId");


--
-- Name: order order_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."order"
    ADD CONSTRAINT order_pkey PRIMARY KEY ("orderId");


--
-- Name: parentChild parentChild_childId_unique; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."parentChild"
    ADD CONSTRAINT "parentChild_childId_unique" UNIQUE ("childId");


--
-- Name: parentChild parentChild_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."parentChild"
    ADD CONSTRAINT "parentChild_pkey" PRIMARY KEY ("parentChildId");


--
-- Name: productAttribute productAttribute_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."productAttribute"
    ADD CONSTRAINT "productAttribute_pkey" PRIMARY KEY ("productAttributeId");


--
-- Name: productImage productImage_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."productImage"
    ADD CONSTRAINT "productImage_pkey" PRIMARY KEY ("productImageId");


--
-- Name: product product_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.product
    ADD CONSTRAINT product_pkey PRIMARY KEY ("productId");


--
-- Name: review review_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.review
    ADD CONSTRAINT review_pkey PRIMARY KEY ("reviewId");


--
-- Name: review review_user_product_unique; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.review
    ADD CONSTRAINT review_user_product_unique UNIQUE ("userId", "productId");


--
-- Name: role role_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.role
    ADD CONSTRAINT role_pkey PRIMARY KEY ("roleId");


--
-- Name: user user_email_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_email_key UNIQUE (email);


--
-- Name: user_groups user_groups_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_groups
    ADD CONSTRAINT user_groups_pkey PRIMARY KEY (id);


--
-- Name: user_groups user_groups_user_id_group_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_groups
    ADD CONSTRAINT user_groups_user_id_group_id_key UNIQUE (user_id, group_id);


--
-- Name: user user_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."user"
    ADD CONSTRAINT user_pkey PRIMARY KEY ("userId");


--
-- Name: user_user_permissions user_user_permissions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_user_permissions
    ADD CONSTRAINT user_user_permissions_pkey PRIMARY KEY (id);


--
-- Name: user_user_permissions user_user_permissions_user_id_permission_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_user_permissions
    ADD CONSTRAINT user_user_permissions_user_id_permission_id_key UNIQUE (user_id, permission_id);


--
-- Name: wishlist wishlist_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wishlist
    ADD CONSTRAINT wishlist_pkey PRIMARY KEY ("wishlistId");


--
-- Name: wishlist wishlist_user_product_unique; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wishlist
    ADD CONSTRAINT wishlist_user_product_unique UNIQUE ("userId", "productId");


--
-- Name: address_userId_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX "address_userId_idx" ON public.address USING btree ("userId");


--
-- Name: auditLog_userId_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX "auditLog_userId_idx" ON public."auditLog" USING btree ("userId");


--
-- Name: auth_group_name_a6ea08ec_like; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX auth_group_name_a6ea08ec_like ON public.auth_group USING btree (name varchar_pattern_ops);


--
-- Name: auth_group_permissions_group_id_b120cbf9; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX auth_group_permissions_group_id_b120cbf9 ON public.auth_group_permissions USING btree (group_id);


--
-- Name: auth_group_permissions_permission_id_84c5c92e; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX auth_group_permissions_permission_id_84c5c92e ON public.auth_group_permissions USING btree (permission_id);


--
-- Name: auth_permission_content_type_id_2f476e4b; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX auth_permission_content_type_id_2f476e4b ON public.auth_permission USING btree (content_type_id);


--
-- Name: authtoken_token_key_10f0b77e_like; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX authtoken_token_key_10f0b77e_like ON public.authtoken_token USING btree (key varchar_pattern_ops);


--
-- Name: cart_productId_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX "cart_productId_idx" ON public.cart USING btree ("productId");


--
-- Name: cart_userId_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX "cart_userId_idx" ON public.cart USING btree ("userId");


--
-- Name: django_admin_log_content_type_id_c4bce8eb; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX django_admin_log_content_type_id_c4bce8eb ON public.django_admin_log USING btree (content_type_id);


--
-- Name: django_admin_log_user_id_c564eba6; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX django_admin_log_user_id_c564eba6 ON public.django_admin_log USING btree (user_id);


--
-- Name: django_session_expire_date_a5c62663; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX django_session_expire_date_a5c62663 ON public.django_session USING btree (expire_date);


--
-- Name: django_session_session_key_c0390e0f_like; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX django_session_session_key_c0390e0f_like ON public.django_session USING btree (session_key varchar_pattern_ops);


--
-- Name: orderItem_orderId_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX "orderItem_orderId_idx" ON public."orderItem" USING btree ("orderId");


--
-- Name: orderItem_productId_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX "orderItem_productId_idx" ON public."orderItem" USING btree ("productId");


--
-- Name: order_addressId_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX "order_addressId_idx" ON public."order" USING btree ("addressId");


--
-- Name: order_orderStatusId_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX "order_orderStatusId_idx" ON public."order" USING btree ("orderStatusId");


--
-- Name: order_userId_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX "order_userId_idx" ON public."order" USING btree ("userId");


--
-- Name: parentChild_childId_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX "parentChild_childId_idx" ON public."parentChild" USING btree ("childId");


--
-- Name: parentChild_userId_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX "parentChild_userId_idx" ON public."parentChild" USING btree ("userId");


--
-- Name: productAttribute_productId_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX "productAttribute_productId_idx" ON public."productAttribute" USING btree ("productId");


--
-- Name: productImage_productId_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX "productImage_productId_idx" ON public."productImage" USING btree ("productId");


--
-- Name: product_brandId_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX "product_brandId_idx" ON public.product USING btree ("brandId");


--
-- Name: product_categoryId_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX "product_categoryId_idx" ON public.product USING btree ("categoryId");


--
-- Name: review_productId_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX "review_productId_idx" ON public.review USING btree ("productId");


--
-- Name: review_userId_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX "review_userId_idx" ON public.review USING btree ("userId");


--
-- Name: user_email_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX user_email_idx ON public."user" USING btree (email);


--
-- Name: user_groups_group_id_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX user_groups_group_id_idx ON public.user_groups USING btree (group_id);


--
-- Name: user_groups_user_id_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX user_groups_user_id_idx ON public.user_groups USING btree (user_id);


--
-- Name: user_roleId_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX "user_roleId_idx" ON public."user" USING btree ("roleId");


--
-- Name: user_user_permissions_permission_id_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX user_user_permissions_permission_id_idx ON public.user_user_permissions USING btree (permission_id);


--
-- Name: user_user_permissions_user_id_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX user_user_permissions_user_id_idx ON public.user_user_permissions USING btree (user_id);


--
-- Name: wishlist_productId_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX "wishlist_productId_idx" ON public.wishlist USING btree ("productId");


--
-- Name: wishlist_userId_idx; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX "wishlist_userId_idx" ON public.wishlist USING btree ("userId");


--
-- Name: order trg_order_audit; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_order_audit AFTER INSERT OR DELETE OR UPDATE ON public."order" FOR EACH ROW EXECUTE FUNCTION public.fn_audit_log();


--
-- Name: product trg_product_audit; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_product_audit AFTER INSERT OR DELETE OR UPDATE ON public.product FOR EACH ROW EXECUTE FUNCTION public.fn_audit_log();


--
-- Name: review trg_review_updated_at; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_review_updated_at BEFORE UPDATE ON public.review FOR EACH ROW EXECUTE FUNCTION public.fn_review_update_timestamp();


--
-- Name: user trg_user_audit; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER trg_user_audit AFTER INSERT OR DELETE OR UPDATE ON public."user" FOR EACH ROW EXECUTE FUNCTION public.fn_audit_log();


--
-- Name: address address_userId_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.address
    ADD CONSTRAINT "address_userId_fk" FOREIGN KEY ("userId") REFERENCES public."user"("userId") ON DELETE CASCADE;


--
-- Name: auditLog auditLog_userId_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."auditLog"
    ADD CONSTRAINT "auditLog_userId_fk" FOREIGN KEY ("userId") REFERENCES public."user"("userId") ON DELETE CASCADE;


--
-- Name: auth_group_permissions auth_group_permissio_permission_id_84c5c92e_fk_auth_perm; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_group_permissions
    ADD CONSTRAINT auth_group_permissio_permission_id_84c5c92e_fk_auth_perm FOREIGN KEY (permission_id) REFERENCES public.auth_permission(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_group_permissions auth_group_permissions_group_id_b120cbf9_fk_auth_group_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_group_permissions
    ADD CONSTRAINT auth_group_permissions_group_id_b120cbf9_fk_auth_group_id FOREIGN KEY (group_id) REFERENCES public.auth_group(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: auth_permission auth_permission_content_type_id_2f476e4b_fk_django_co; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.auth_permission
    ADD CONSTRAINT auth_permission_content_type_id_2f476e4b_fk_django_co FOREIGN KEY (content_type_id) REFERENCES public.django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: authtoken_token authtoken_token_user_id_35299eff_fk_user_userId; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.authtoken_token
    ADD CONSTRAINT "authtoken_token_user_id_35299eff_fk_user_userId" FOREIGN KEY (user_id) REFERENCES public."user"("userId") DEFERRABLE INITIALLY DEFERRED;


--
-- Name: cart cart_productId_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.cart
    ADD CONSTRAINT "cart_productId_fk" FOREIGN KEY ("productId") REFERENCES public.product("productId") ON DELETE CASCADE;


--
-- Name: cart cart_userId_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.cart
    ADD CONSTRAINT "cart_userId_fk" FOREIGN KEY ("userId") REFERENCES public."user"("userId") ON DELETE CASCADE;


--
-- Name: django_admin_log django_admin_log_content_type_id_c4bce8eb_fk_django_co; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_admin_log
    ADD CONSTRAINT django_admin_log_content_type_id_c4bce8eb_fk_django_co FOREIGN KEY (content_type_id) REFERENCES public.django_content_type(id) DEFERRABLE INITIALLY DEFERRED;


--
-- Name: django_admin_log django_admin_log_user_id_c564eba6_fk_user_userId; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.django_admin_log
    ADD CONSTRAINT "django_admin_log_user_id_c564eba6_fk_user_userId" FOREIGN KEY (user_id) REFERENCES public."user"("userId") DEFERRABLE INITIALLY DEFERRED;


--
-- Name: orderItem orderItem_orderId_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."orderItem"
    ADD CONSTRAINT "orderItem_orderId_fk" FOREIGN KEY ("orderId") REFERENCES public."order"("orderId") ON DELETE CASCADE;


--
-- Name: orderItem orderItem_productId_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."orderItem"
    ADD CONSTRAINT "orderItem_productId_fk" FOREIGN KEY ("productId") REFERENCES public.product("productId") ON DELETE CASCADE;


--
-- Name: order order_addressId_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."order"
    ADD CONSTRAINT "order_addressId_fk" FOREIGN KEY ("addressId") REFERENCES public.address("addressId") ON DELETE CASCADE;


--
-- Name: order order_orderStatusId_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."order"
    ADD CONSTRAINT "order_orderStatusId_fk" FOREIGN KEY ("orderStatusId") REFERENCES public."orderStatus"("orderStatusId") ON DELETE CASCADE;


--
-- Name: order order_userId_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."order"
    ADD CONSTRAINT "order_userId_fk" FOREIGN KEY ("userId") REFERENCES public."user"("userId") ON DELETE CASCADE;


--
-- Name: parentChild parentChild_childId_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."parentChild"
    ADD CONSTRAINT "parentChild_childId_fk" FOREIGN KEY ("childId") REFERENCES public."user"("userId") ON DELETE CASCADE;


--
-- Name: parentChild parentChild_userId_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."parentChild"
    ADD CONSTRAINT "parentChild_userId_fk" FOREIGN KEY ("userId") REFERENCES public."user"("userId") ON DELETE CASCADE;


--
-- Name: productAttribute productAttribute_productId_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."productAttribute"
    ADD CONSTRAINT "productAttribute_productId_fk" FOREIGN KEY ("productId") REFERENCES public.product("productId") ON DELETE CASCADE;


--
-- Name: productImage productImage_productId_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."productImage"
    ADD CONSTRAINT "productImage_productId_fk" FOREIGN KEY ("productId") REFERENCES public.product("productId") ON DELETE CASCADE;


--
-- Name: product product_brandId_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.product
    ADD CONSTRAINT "product_brandId_fk" FOREIGN KEY ("brandId") REFERENCES public.brand("brandId") ON DELETE CASCADE;


--
-- Name: product product_categoryId_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.product
    ADD CONSTRAINT "product_categoryId_fk" FOREIGN KEY ("categoryId") REFERENCES public.category("categoryId") ON DELETE CASCADE;


--
-- Name: review review_productId_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.review
    ADD CONSTRAINT "review_productId_fk" FOREIGN KEY ("productId") REFERENCES public.product("productId") ON DELETE CASCADE;


--
-- Name: review review_userId_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.review
    ADD CONSTRAINT "review_userId_fk" FOREIGN KEY ("userId") REFERENCES public."user"("userId") ON DELETE CASCADE;


--
-- Name: user_groups user_groups_user_id_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_groups
    ADD CONSTRAINT user_groups_user_id_fk FOREIGN KEY (user_id) REFERENCES public."user"("userId") ON DELETE CASCADE;


--
-- Name: user user_roleId_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public."user"
    ADD CONSTRAINT "user_roleId_fk" FOREIGN KEY ("roleId") REFERENCES public.role("roleId") ON DELETE CASCADE;


--
-- Name: user_user_permissions user_user_permissions_user_id_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_user_permissions
    ADD CONSTRAINT user_user_permissions_user_id_fk FOREIGN KEY (user_id) REFERENCES public."user"("userId") ON DELETE CASCADE;


--
-- Name: wishlist wishlist_productId_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wishlist
    ADD CONSTRAINT "wishlist_productId_fk" FOREIGN KEY ("productId") REFERENCES public.product("productId") ON DELETE CASCADE;


--
-- Name: wishlist wishlist_userId_fk; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.wishlist
    ADD CONSTRAINT "wishlist_userId_fk" FOREIGN KEY ("userId") REFERENCES public."user"("userId") ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict zvzxXLWDd7FnQJVHT6Mb42qXih8RKDaYaVOUaMX0MGYqpDHxQq1nDuGlxQz79Ob

