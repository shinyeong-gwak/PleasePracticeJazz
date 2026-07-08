--
-- PostgreSQL database dump
--

\restrict wDM3cGkshMaMp63K0aN8s7JyjTadjZIE2YJvsPpOQisodnreAbucaDpA98LCctn

-- Dumped from database version 14.23 (Ubuntu 14.23-0ubuntu0.22.04.1)
-- Dumped by pg_dump version 14.23 (Ubuntu 14.23-0ubuntu0.22.04.1)

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

--
-- Name: pgcrypto; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA public;


--
-- Name: EXTENSION pgcrypto; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION pgcrypto IS 'cryptographic functions';


--
-- Name: insight_category; Type: TYPE; Schema: public; Owner: sygwak
--

CREATE TYPE public.insight_category AS ENUM (
    'RHYTHM',
    'SOLO',
    'VOICING',
    'ENSEMBLE'
);


ALTER TYPE public.insight_category OWNER TO sygwak;

--
-- Name: practice_status; Type: TYPE; Schema: public; Owner: sygwak
--

CREATE TYPE public.practice_status AS ENUM (
    'NORMAL',
    'GOOD',
    'BAD'
);


ALTER TYPE public.practice_status OWNER TO sygwak;

--
-- Name: practice_type; Type: TYPE; Schema: public; Owner: sygwak
--

CREATE TYPE public.practice_type AS ENUM (
    'PRACTICE',
    'ENSEMBLE'
);


ALTER TYPE public.practice_type OWNER TO sygwak;

--
-- Name: score_format; Type: TYPE; Schema: public; Owner: sygwak
--

CREATE TYPE public.score_format AS ENUM (
    'MUSICXML',
    'MIDI',
    'LILYPOND',
    'CUSTOM'
);


ALTER TYPE public.score_format OWNER TO sygwak;

--
-- Name: week_start_day; Type: TYPE; Schema: public; Owner: sygwak
--

CREATE TYPE public.week_start_day AS ENUM (
    'SUNDAY',
    'MONDAY',
    'TUESDAY',
    'WEDNESDAY',
    'THURSDAY',
    'FRIDAY',
    'SATURDAY'
);


ALTER TYPE public.week_start_day OWNER TO sygwak;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: app_user; Type: TABLE; Schema: public; Owner: sygwak
--

CREATE TABLE public.app_user (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    nickname text NOT NULL,
    email text,
    username text,
    password_hash text,
    terms_accepted_at timestamp with time zone,
    week_start_day public.week_start_day DEFAULT 'MONDAY'::public.week_start_day NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.app_user OWNER TO sygwak;

--
-- Name: clip; Type: TABLE; Schema: public; Owner: sygwak
--

CREATE TABLE public.clip (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    playlist_item_id uuid NOT NULL,
    name text NOT NULL,
    key text,
    time_signature text,
    chords text,
    degrees text,
    melody text,
    melody_rhythm text,
    voicing text,
    voicing_rhythm text,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    file_name text,
    file_path text
);


ALTER TABLE public.clip OWNER TO sygwak;

--
-- Name: insight; Type: TABLE; Schema: public; Owner: sygwak
--

CREATE TABLE public.insight (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    category public.insight_category NOT NULL,
    content text NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.insight OWNER TO sygwak;

--
-- Name: lick; Type: TABLE; Schema: public; Owner: sygwak
--

CREATE TABLE public.lick (
    id uuid NOT NULL,
    user_id uuid NOT NULL,
    clip_id uuid,
    name text NOT NULL,
    key text,
    time_signature text,
    chords text,
    degrees text,
    melody text,
    melody_rhythm text,
    voicing text,
    voicing_rhythm text,
    created_at timestamp without time zone DEFAULT now(),
    updated_at timestamp without time zone DEFAULT now()
);


ALTER TABLE public.lick OWNER TO sygwak;

--
-- Name: playlist; Type: TABLE; Schema: public; Owner: sygwak
--

CREATE TABLE public.playlist (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    name text NOT NULL,
    source_url text NOT NULL,
    last_sync_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.playlist OWNER TO sygwak;

--
-- Name: playlist_item; Type: TABLE; Schema: public; Owner: sygwak
--

CREATE TABLE public.playlist_item (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    playlist_id uuid NOT NULL,
    file_name text NOT NULL,
    file_path text NOT NULL,
    source_url text,
    duration_sec integer,
    downloaded_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    youtube_video_id text,
    title text
);


ALTER TABLE public.playlist_item OWNER TO sygwak;

--
-- Name: practice_item; Type: TABLE; Schema: public; Owner: sygwak
--

CREATE TABLE public.practice_item (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    type public.practice_type NOT NULL,
    title text NOT NULL,
    bpm integer,
    book text,
    page text,
    memo text,
    spotify_url text,
    metronome boolean DEFAULT false NOT NULL,
    status public.practice_status DEFAULT 'NORMAL'::public.practice_status NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    lick_id uuid,
    score_id uuid
);


ALTER TABLE public.practice_item OWNER TO sygwak;

--
-- Name: practice_topic; Type: TABLE; Schema: public; Owner: sygwak
--

CREATE TABLE public.practice_topic (
    practice_id uuid NOT NULL,
    topic_id uuid NOT NULL
);


ALTER TABLE public.practice_topic OWNER TO sygwak;

--
-- Name: score; Type: TABLE; Schema: public; Owner: sygwak
--

CREATE TABLE public.score (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    lick_id uuid NOT NULL,
    name text NOT NULL,
    format public.score_format DEFAULT 'MUSICXML'::public.score_format NOT NULL,
    file_path text NOT NULL,
    file_name text,
    version integer DEFAULT 1 NOT NULL,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL,
    original_file_name text
);


ALTER TABLE public.score OWNER TO sygwak;

--
-- Name: topic; Type: TABLE; Schema: public; Owner: sygwak
--

CREATE TABLE public.topic (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    name text NOT NULL
);


ALTER TABLE public.topic OWNER TO sygwak;

--
-- Name: user_settings; Type: TABLE; Schema: public; Owner: sygwak
--

CREATE TABLE public.user_settings (
    user_id uuid NOT NULL,
    locale text DEFAULT 'ko-KR'::text,
    time_zone text DEFAULT 'Asia/Seoul'::text NOT NULL,
    week_start_day integer DEFAULT 1 NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    updated_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.user_settings OWNER TO sygwak;

--
-- Name: weekly_goal; Type: TABLE; Schema: public; Owner: sygwak
--

CREATE TABLE public.weekly_goal (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id uuid NOT NULL,
    title text NOT NULL,
    memo text,
    status public.practice_status DEFAULT 'NORMAL'::public.practice_status NOT NULL,
    completed_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT now() NOT NULL,
    updated_at timestamp with time zone DEFAULT now() NOT NULL
);


ALTER TABLE public.weekly_goal OWNER TO sygwak;

--
-- Name: app_user app_user_pkey; Type: CONSTRAINT; Schema: public; Owner: sygwak
--

ALTER TABLE ONLY public.app_user
    ADD CONSTRAINT app_user_pkey PRIMARY KEY (id);


--
-- Name: insight insight_pkey; Type: CONSTRAINT; Schema: public; Owner: sygwak
--

ALTER TABLE ONLY public.insight
    ADD CONSTRAINT insight_pkey PRIMARY KEY (id);


--
-- Name: clip lick_pkey; Type: CONSTRAINT; Schema: public; Owner: sygwak
--

ALTER TABLE ONLY public.clip
    ADD CONSTRAINT lick_pkey PRIMARY KEY (id);


--
-- Name: lick lick_pkey1; Type: CONSTRAINT; Schema: public; Owner: sygwak
--

ALTER TABLE ONLY public.lick
    ADD CONSTRAINT lick_pkey1 PRIMARY KEY (id);


--
-- Name: playlist_item playlist_item_pkey; Type: CONSTRAINT; Schema: public; Owner: sygwak
--

ALTER TABLE ONLY public.playlist_item
    ADD CONSTRAINT playlist_item_pkey PRIMARY KEY (id);


--
-- Name: playlist playlist_pkey; Type: CONSTRAINT; Schema: public; Owner: sygwak
--

ALTER TABLE ONLY public.playlist
    ADD CONSTRAINT playlist_pkey PRIMARY KEY (id);


--
-- Name: practice_item practice_item_pkey; Type: CONSTRAINT; Schema: public; Owner: sygwak
--

ALTER TABLE ONLY public.practice_item
    ADD CONSTRAINT practice_item_pkey PRIMARY KEY (id);


--
-- Name: practice_topic practice_topic_pkey; Type: CONSTRAINT; Schema: public; Owner: sygwak
--

ALTER TABLE ONLY public.practice_topic
    ADD CONSTRAINT practice_topic_pkey PRIMARY KEY (practice_id, topic_id);


--
-- Name: score score_pkey; Type: CONSTRAINT; Schema: public; Owner: sygwak
--

ALTER TABLE ONLY public.score
    ADD CONSTRAINT score_pkey PRIMARY KEY (id);


--
-- Name: topic topic_name_key; Type: CONSTRAINT; Schema: public; Owner: sygwak
--

ALTER TABLE ONLY public.topic
    ADD CONSTRAINT topic_name_key UNIQUE (name);


--
-- Name: topic topic_pkey; Type: CONSTRAINT; Schema: public; Owner: sygwak
--

ALTER TABLE ONLY public.topic
    ADD CONSTRAINT topic_pkey PRIMARY KEY (id);


--
-- Name: user_settings user_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: sygwak
--

ALTER TABLE ONLY public.user_settings
    ADD CONSTRAINT user_settings_pkey PRIMARY KEY (user_id);


--
-- Name: weekly_goal weekly_goal_pkey; Type: CONSTRAINT; Schema: public; Owner: sygwak
--

ALTER TABLE ONLY public.weekly_goal
    ADD CONSTRAINT weekly_goal_pkey PRIMARY KEY (id);


--
-- Name: idx_insight_user_category; Type: INDEX; Schema: public; Owner: sygwak
--

CREATE INDEX idx_insight_user_category ON public.insight USING btree (user_id, category);


--
-- Name: app_user_email_lower_key; Type: INDEX; Schema: public; Owner: sygwak
--

CREATE UNIQUE INDEX app_user_email_lower_key ON public.app_user USING btree (lower(email)) WHERE (email IS NOT NULL);


--
-- Name: app_user_username_lower_key; Type: INDEX; Schema: public; Owner: sygwak
--

CREATE UNIQUE INDEX app_user_username_lower_key ON public.app_user USING btree (lower(username)) WHERE (username IS NOT NULL);


--
-- Name: idx_lick_item; Type: INDEX; Schema: public; Owner: sygwak
--

CREATE INDEX idx_lick_item ON public.clip USING btree (playlist_item_id);


--
-- Name: idx_lick_user; Type: INDEX; Schema: public; Owner: sygwak
--

CREATE INDEX idx_lick_user ON public.clip USING btree (user_id);


--
-- Name: idx_playlist_item_playlist; Type: INDEX; Schema: public; Owner: sygwak
--

CREATE INDEX idx_playlist_item_playlist ON public.playlist_item USING btree (playlist_id);


--
-- Name: idx_practice_type; Type: INDEX; Schema: public; Owner: sygwak
--

CREATE INDEX idx_practice_type ON public.practice_item USING btree (type);


--
-- Name: idx_score_lick; Type: INDEX; Schema: public; Owner: sygwak
--

CREATE INDEX idx_score_lick ON public.score USING btree (lick_id);


--
-- Name: idx_weekly_goal_user; Type: INDEX; Schema: public; Owner: sygwak
--

CREATE INDEX idx_weekly_goal_user ON public.weekly_goal USING btree (user_id);


--
-- Name: insight insight_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: sygwak
--

ALTER TABLE ONLY public.insight
    ADD CONSTRAINT insight_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.app_user(id) ON DELETE CASCADE;


--
-- Name: clip lick_playlist_item_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: sygwak
--

ALTER TABLE ONLY public.clip
    ADD CONSTRAINT lick_playlist_item_id_fkey FOREIGN KEY (playlist_item_id) REFERENCES public.playlist_item(id) ON DELETE CASCADE;


--
-- Name: clip lick_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: sygwak
--

ALTER TABLE ONLY public.clip
    ADD CONSTRAINT lick_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.app_user(id) ON DELETE CASCADE;


--
-- Name: playlist_item playlist_item_playlist_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: sygwak
--

ALTER TABLE ONLY public.playlist_item
    ADD CONSTRAINT playlist_item_playlist_id_fkey FOREIGN KEY (playlist_id) REFERENCES public.playlist(id) ON DELETE CASCADE;


--
-- Name: playlist playlist_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: sygwak
--

ALTER TABLE ONLY public.playlist
    ADD CONSTRAINT playlist_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.app_user(id) ON DELETE CASCADE;


--
-- Name: practice_item practice_item_lick_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: sygwak
--

ALTER TABLE ONLY public.practice_item
    ADD CONSTRAINT practice_item_lick_id_fkey FOREIGN KEY (lick_id) REFERENCES public.clip(id);


--
-- Name: practice_item practice_item_score_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: sygwak
--

ALTER TABLE ONLY public.practice_item
    ADD CONSTRAINT practice_item_score_id_fkey FOREIGN KEY (score_id) REFERENCES public.score(id);


--
-- Name: practice_item practice_item_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: sygwak
--

ALTER TABLE ONLY public.practice_item
    ADD CONSTRAINT practice_item_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.app_user(id) ON DELETE CASCADE;


--
-- Name: practice_topic practice_topic_practice_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: sygwak
--

ALTER TABLE ONLY public.practice_topic
    ADD CONSTRAINT practice_topic_practice_id_fkey FOREIGN KEY (practice_id) REFERENCES public.practice_item(id) ON DELETE CASCADE;


--
-- Name: practice_topic practice_topic_topic_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: sygwak
--

ALTER TABLE ONLY public.practice_topic
    ADD CONSTRAINT practice_topic_topic_id_fkey FOREIGN KEY (topic_id) REFERENCES public.topic(id) ON DELETE CASCADE;


--
-- Name: score score_lick_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: sygwak
--

ALTER TABLE ONLY public.score
    ADD CONSTRAINT score_lick_id_fkey FOREIGN KEY (lick_id) REFERENCES public.clip(id) ON DELETE CASCADE;


--
-- Name: score score_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: sygwak
--

ALTER TABLE ONLY public.score
    ADD CONSTRAINT score_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.app_user(id) ON DELETE CASCADE;


--
-- Name: user_settings user_settings_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: sygwak
--

ALTER TABLE ONLY public.user_settings
    ADD CONSTRAINT user_settings_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.app_user(id) ON DELETE CASCADE;


--
-- Name: weekly_goal weekly_goal_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: sygwak
--

ALTER TABLE ONLY public.weekly_goal
    ADD CONSTRAINT weekly_goal_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.app_user(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict wDM3cGkshMaMp63K0aN8s7JyjTadjZIE2YJvsPpOQisodnreAbucaDpA98LCctn
