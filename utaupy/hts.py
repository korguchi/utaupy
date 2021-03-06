#! /usr/bin/env python3
# coding: utf-8
# Copyright (c) 2020 oatsu
"""
Python3 module for HTS-full-label.
"""

import re
# from collections import UserList
from itertools import chain
from pprint import pprint

# import itertools


def load(source):
    """
    HTSフルコンテキストラベル(Sinsy用)を読み取る

    source: path, lines
    """
    song = HTSFullLabel()
    return song.load(source)


class HTSFullLabel(list):
    """
    HTSのフルコンテキストラベルの1行を扱うクラス
    OneLine からなる list
    [OneLine, OneLine, ..., OneLine]
    """

    def __init__(self):
        super().__init__()
        self.song = Song()

    def write(self, path, mode='w', encoding='utf-8') -> str:
        """
        ファイル出力する
        """
        s = '\n'.join([str(oneline) for oneline in self])
        with open(path, mode=mode, encoding=encoding) as f:
            f.write(s)
        return s

    def load(self, source, encoding='utf-8'):
        """
        ファイル、文字列、文字列のリスト、Songオブジェクトのいずれかより値を取得して登録する。
        """
        if isinstance(source, str):
            self._load_from_path(source, encoding=encoding)
        elif type(source) == Song:
            self._load_from_songobj(source)
        elif type(source) == list:
            self._load_from_lines(source)
        else:
            raise TypeError(f'Type of the argument "source" must be str, list or {Song}.')
        self.song = self.as_song()
        # self.fill_contexts_from_songobj()
        return self

    def _load_from_path(self, path, encoding: str = 'utf-8'):
        """
        ファイルをもとに値を登録する。
        """
        # パスに半角スペースが入っている場合に出現する引用符を除去
        path = path.strip('"')
        # ファイルを読み取って行のリストにする
        try:
            with open(path, mode='r', encoding=encoding) as f:
                lines = [line.rstrip('\r\n') for line in f.readlines()]
        except UnicodeDecodeError:
            with open(path, mode='r', encoding='sjis') as f:
                lines = [line.rstrip('\r\n') for line in f.readlines()]
        # 行ごとに分割したリストをもとに情報を登録する。
        self._load_from_lines(lines)
        return self

    def _load_from_lines(self, lines: list):
        """
        文字列のリスト(行のリスト)をもとに値を登録する。
        """
        # 各行を解析してHTSFullLabelに追加する。
        for line in lines:
            # 1行分の情報用のオブジェクトを生成
            oneline = _OneLine()
            # 正規表現で上手く区切れない文字を置換する
            # 空白で分割して、時刻情報とそれ以外のコンテキストに分ける
            line_split = line.split(maxsplit=2)
            oneline.start = int(line_split[0])
            oneline.end = int(line_split[1])
            str_contexts = line_split[2]
            # コンテキスト文字列を /A: などの文字列で区切って一次元リストにする
            l_contexts = re.split('/.:', str_contexts)
            # 特定の文字でさらに区切って二次元リストにする
            sep = re.escape('=+-~∼!@#$%^ˆ&;_|[]')
            l_contexts_2d = [re.split((f'[{sep}]'), s) for s in l_contexts]
            # 1行分の情報用のオブジェクトに、各種コンテキストを登録する
            oneline.p = l_contexts_2d[0]
            oneline.a = l_contexts_2d[1]
            oneline.b = l_contexts_2d[2]
            oneline.c = l_contexts_2d[3]
            oneline.d = l_contexts_2d[4]
            oneline.e = l_contexts_2d[5]
            oneline.f = l_contexts_2d[6]
            oneline.g = l_contexts_2d[7]
            oneline.h = l_contexts_2d[8]
            oneline.i = l_contexts_2d[9]
            oneline.j = l_contexts_2d[10]
            # 1行分の情報用のオブジェクトを HTSFullLabel オブジェクトに追加する。
            self.append(oneline)
        return self

    def _load_from_songobj(self, songobj: list):
        """
        hts.Song オブジェクトをもとにコンテキストを登録する。
        """
        self.song = songobj
        self.fill_contexts_from_songobj()
        return self

    def fill_contexts_from_songobj(self):
        """
        自身が持つSongオブジェクトをもとにコンテキスト情報を埋める。
        {object_name}_current 系のオブジェクトのみから前後を補完する。
        """
        song = self.song
        phrases = [Phrase()] + song + [Phrase()]
        for i_p, phrase in enumerate(phrases[1:-1], 1):
            notes = phrases[i_p - 1][-1] + phrase + phrases[i_p + 1][0]
            for i_n, note in enumerate(notes[1:-1], 1):
                syllables = notes[i_n - 1][-1] + phrase + notes[i_n + 1][0]
                for i_s, syllable in enumerate(syllables[1:-1], 1):
                    for phoneme in syllable:
                        # TODO: ここ消す
                        print(list(map(id, [phoneme, note, syllable, phoneme])))
                        ol = _OneLine()
                        # 音素情報を登録(現在の音素のみ)
                        ol.phoneme = phoneme
                        # 音節情報を登録
                        ol.syllable = syllable
                        ol.syllable_previous = syllables[i_s - 1]
                        ol.syllable_next = syllables[i_s - 1]
                        # ノート情報を登録
                        ol.note = note
                        ol.note_previous = notes[i_n - 1]
                        ol.note_next = notes[i_n + 1]
                        # フレーズ情報を登録
                        ol.phrase = phrase
                        ol.phrase_previous = phrases[i_p - 1]
                        ol.phrase_next = phrases[i_p + 1]
                        # 楽曲情報を登録
                        ol.song = song
        self._fill_phoneme_contexts()
        return self

    def _fill_phoneme_contexts(self):
        """
        phoneme をもとに、前後の音素に関する項を埋める。
        """
        extended_self = [_OneLine(), _OneLine()] + self + [_OneLine(), _OneLine()]
        # ol is OneLine objec
        for i, ol in enumerate(extended_self[2:-2], 2):
            ol.phoneme_before_previous = extended_self[i - 2].phoneme
            ol.phoneme_previous = extended_self[i - 1].phoneme
            ol.phoneme_next = extended_self[i + 1].phoneme
            ol.phoneme_after_next = extended_self[i + 2].phoneme
        return self

    def as_song(self):
        """
        フルコンテキストラベルの情報をもとにSongオブジェクトをつくる。
        self.song に格納する。
        """
        # Song は1つの HTSFullLabel につき1つだけなので、ループする必要がない。
        # Song は一番最初の行の情報がすべての行に通用すると考える。
        song = self[0].song
        phrase = Phrase()
        note = Note()
        syllable = Syllable()
        for ol in self:
            phoneme = ol.phoneme
            # ノートが「フレーズ内で1番最初のノート」なとき、フレーズを切り替える。
            if str(ol.note.position) in ('xx', '1'):
                phrase = ol.phrase
                song.append(phrase)
            # 音節が「ノート内で1番最初の音節」なとき、ノートを切り替える。
            if str(ol.syllable.position) == '1':
                note = ol.note
                phrase.append(note)
            # 音素が「音節内で1番最初の音素」なとき、音節を切り替える。
            if str(phoneme.position) == '1':
                syllable = ol.syllable
                note.append(syllable)
            syllable.append(phoneme)
            print(phoneme.identity, syllable.position, note.position)
            for note in phrase:
                for syllable in note:
                    for phoneme in syllable:
                        print('len(song)', len(song))
                        print('phrase\t', phrase)
                        print('note\t', note)
                        print('syllable', syllable)
                        print('phoneme\t', phoneme)
                        print('------------------------------------------------------------------------------')
        # song.check()
        return song


class _OneLine:
    """
    HTSのフルコンテキストラベルの1行を扱うクラス
    ファイルを読み取って HTSFullLabel を生成するときと、
    HTSFullLabel をファイル入出力するときに使う。
    """

    def __init__(self):
        self.phoneme_before_previous = Phoneme()
        self.phoneme_previous = Phoneme()
        self.phoneme = Phoneme()
        self.phoneme_next = Phoneme()
        self.phoneme_after_next = Phoneme()
        self.syllable_previous = Syllable()
        self.syllable = Syllable()
        self.syllable_next = Syllable()
        self.note_previous = Note()
        self.note = Note()
        self.note_next = Note()
        self.phrase_previous = Phrase()
        self.phrase = Phrase()
        self.phrase_next = Phrase()
        self.song = Song()

    def __str__(self):
        str_time = f'{self.start} {self.end} '
        # Phoneme 関連
        str_p = \
            '{0}@{1}ˆ{2}-{3}+{4}={5}_{6}%{7}ˆ{8}_{9}∼{10}-{11}!{12}[{13}${14}]{15}' \
            .format(*self.p)
        # Syllable 関連
        str_a = '/A:{0}-{1}-{2}@{3}~{4}'.format(*self.a)
        str_b = '/B:{0}_{1}_{2}@{3}|{4}'.format(*self.b)
        str_c = '/C:{0}+{1}+{2}@{3}&{4}'.format(*self.c)
        # Note 関連
        str_d = '/D:{0}!{1}#{2}${3}%{4}|{5}&{6};{7}-{8}'.format(*self.d)
        str_e = \
            '/E:{0}]{1}ˆ{2}={3}∼{4}!{5}@{6}#{7}+{8}]{9}${10}|{11}[{12}&{13}]{14}={15}ˆ{16}∼{17}#{18}_{19};{20}${21}&{22}%{23}[{24}|{25}]{26}-{27}ˆ{28}+{29}∼{30}={31}@{32}${33}!{34}%{35}#{36}|{37}|{38}-{39}&{40}&{41}+{42}[{43};{44}]{45};{46}∼{47}∼{48}ˆ{49}ˆ{50}@{51}[{52}#{53}={54}!{55}∼{56}+{57}!{58}ˆ{59}' \
            .format(*self.e)
        str_f = '/F:{0}#{1}#{2}-{3}${4}${5}+{6}%{7};{8}'.format(*self.f)
        # Phrase 関連
        str_g = '/G:{0}_{1}'.format(*self.g)
        str_h = '/H:{0}_{1}'.format(*self.h)
        str_i = '/I:{0}_{1}'.format(*self.i)
        # Song 関連
        str_j = '/J:{0}~{1}@{2}'.format(*self.j)
        # 各パラメータの文字列を結合
        str_self = ''.join((str_time, str_p, str_a, str_b, str_c, str_d,
                            str_e, str_f, str_g, str_h, str_i, str_j))
        return str_self

    @property
    def start(self) -> int:
        """
        発声開始時刻
        """
        return int(self.phoneme.start)

    @start.setter
    def start(self, start_time: int):
        self.phoneme.start = int(start_time)

    @property
    def end(self) -> int:
        """
        発声終了時刻
        """
        return int(self.phoneme.end)

    @end.setter
    def end(self, end_time: int):
        self.phoneme.end = int(end_time)

    @property
    def p(self) -> list:
        """
        音素に関するコンテキスト
        """
        p = [
            self.phoneme.language_independent_identity,
            self.phoneme_before_previous.identity,
            self.phoneme_previous.identity,
            self.phoneme.identity,
            self.phoneme_next.identity,
            self.phoneme_after_next.identity,
            self.phoneme_before_previous.flag,
            self.phoneme_previous.flag,
            self.phoneme.flag,
            self.phoneme_next.flag,
            self.phoneme_after_next.flag,
            self.phoneme.position,
            self.phoneme.position_backward,
            self.phoneme.distance_from_previous_vowel,
            self.phoneme.distance_to_next_vowel,
            self.phoneme.undefined_context
        ]
        return p

    @p.setter
    def p(self, phoneme_contexts: list):
        self.phoneme.language_independent_identity = phoneme_contexts[0]
        self.phoneme_before_previous.identity = phoneme_contexts[1]
        self.phoneme_previous.identity = phoneme_contexts[2]
        self.phoneme.identity = phoneme_contexts[3]
        self.phoneme_next.identity = phoneme_contexts[4]
        self.phoneme_after_next.identity = phoneme_contexts[5]
        self.phoneme_before_previous.flag = phoneme_contexts[6]
        self.phoneme_previous.flag = phoneme_contexts[7]
        self.phoneme.flag = phoneme_contexts[8]
        self.phoneme_next.flag = phoneme_contexts[9]
        self.phoneme_after_next.flag = phoneme_contexts[10]
        self.phoneme.position = phoneme_contexts[11]
        self.phoneme.position_backward = phoneme_contexts[12]
        self.phoneme.distance_from_previous_vowel = phoneme_contexts[13]
        self.phoneme.distance_to_next_vowel = phoneme_contexts[14]
        self.phoneme.undefined_context = phoneme_contexts[15]

    @property
    def a(self) -> list:
        """
        直前の音節のコンテキスト
        """
        return self.syllable_previous.contexts

    @a.setter
    def a(self, syllable_contexts: list):
        self.syllable_previous.contexts = syllable_contexts

    @property
    def b(self) -> list:
        """
        現在の音節のコンテキスト
        """
        return self.syllable.contexts

    @b.setter
    def b(self, syllable_contexts: list):
        self.syllable.contexts = syllable_contexts

    @property
    def c(self) -> list:
        """
        直後の音節のコンテキスト
        """
        return self.syllable_next.contexts

    @c.setter
    def c(self, syllable_contexts: list):
        self.syllable_next.contexts = syllable_contexts

    @property
    def d(self) -> list:
        """
        直前のノートのコンテキスト
        """
        return self.note_previous.contexts

    @d.setter
    def d(self, note_contexts: list):
        self.note_previous.contexts = note_contexts

    @property
    def e(self) -> list:
        """
        現在のノートのコンテキスト
        """
        return self.note.contexts

    @e.setter
    def e(self, note_contexts: list):
        self.note.contexts = note_contexts

    @property
    def f(self) -> list:
        """
        直後のノートのコンテキスト
        """
        return self.note_next.contexts

    @f.setter
    def f(self, note_contexts: list):
        self.note_next.contexts = note_contexts

    @property
    def g(self) -> list:
        """
        直前のフレーズのコンテキスト
        """
        return self.phrase_previous.contexts

    @g.setter
    def g(self, phrase_contexts: list):
        self.phrase_previous.contexts = phrase_contexts

    @property
    def h(self) -> list:
        """
        現在のフレーズのコンテキスト
        """
        return self.phrase.contexts

    @h.setter
    def h(self, phrase_contexts: list):
        self.phrase.contexts = phrase_contexts

    @property
    def i(self) -> list:
        """
        直後のフレーズのコンテキスト
        """
        return self.phrase_next.contexts

    @i.setter
    def i(self, phrase_contexts: list):
        self.phrase_next.contexts = phrase_contexts

    @property
    def j(self) -> list:
        """
        (現在の)楽曲のコンテキスト
        1ファイル1曲。
        """
        return self.song.contexts

    @j.setter
    def j(self, song_contexts: list):
        self.song.contexts = song_contexts


class Song(list):
    """
    曲を扱うクラス
    今日の曲(j1-j3)
    [Phrase, Phrase, ..., Phrase]
    """

    def __init__(self):
        super().__init__()
        self.contexts = ['xx'] * 3
        self.number_of_measures = 'xx'

    @property
    def all_phrases(self):
        """
        Phraseをすべて並べたリストを返す。
        """
        return self

    @property
    def all_notes(self):
        """
        Noteをすべて並べたリストを返す。
        """
        return list(chain.from_iterable(self))

    @property
    def all_syllables(self):
        """
        Syllableをすべて並べたリストを返す。
        """
        return list(chain.from_iterable(self.all_notes))

    @property
    def all_phonemes(self):
        """
        Phonemeをすべて並べたリストを返す。
        """
        return list(chain.from_iterable(self.all_syllables))

    @property
    def number_of_phrases(self):
        """
        楽曲内のフレーズ数。(j3)
        _OneLine から Song を生成するときにつかう。
        """
        return self.contexts[2]

    @number_of_phrases.setter
    def number_of_phrases(self, number: int):
        self.contexts[2] = int(number)

    def check(self):
        """
        まとめてチェックする。
        """
        self.check_number_of_values()
        self.check_position()

    def check_number_of_values(self):
        """
        リストとしての要素数と、コンテキストに記載されている要素数が一致するか点検する。
        Noteに記載されている
        """
        # 各要素数がちゃんとしているか確認する。
        # 楽曲内フレーズ数が、ラベルに記載されている値と一致するか確認する。
        assert len(self) == self.number_of_phrases, \
            f'楽曲内フレーズ数に不整合があります。len(Song):{len(self)}, ラベル記載値: {self.number_of_phrases}'
        # フレーズ内の値をチェック
        for phrase in self.all_phrases:
            syllables = list(chain.from_iterable(phrase))
            # 各フレーズ内音節数が、ラベルに記載されている値と一致するか確認する。
            assert len(syllables) == phrase.number_of_syllables, \
                f'フレーズ内音節数に不整合があります。{len(syllables)}, {phrase.number_of_syllables}'
            # 各フレーズ内音素数が、ラベルに記載されている値と一致するか確認する。
            assert sum(list(map(len, syllables))) == phrase.number_of_phonemes, \
                'フレーズ内音素数に不整合があります。'
        # 各音節内音素数が、ラベルに記載されている値と一致するか確認する。
        assert all(len(syllable) == syllable.number_of_phonemes for syllable in self.all_syllables), \
            '音節内音素数に不整合があります。'

    def check_position(self):
        """
        各position がちゃんとしているか確認する。
        """
        for syllable in self.all_syllables:
            assert all(phoneme.position == idx + 1 for (phoneme, idx) in enumerate(syllable)), \
                '音節内音素位置に不整合があります。'
        for note in self.all_notes:
            assert all(syllable.position == idx + 1 for (syllable, idx) in enumerate(note)), \
                'ノート内音節位置に不整合があります。'
        for phrase in self.all_phrases:
            assert all(note.position == idx + 1 for (note, idx) in enumerate(phrase)), \
                'フレーズ内ノート位置に不整合があります。'


class Phrase(list):
    """
    フレーズを扱うクラス
    昨日のフレーズ G (g1~g2)
    今日のフレーズ H (h1~h2)
    明日のフレーズ I (i1~i2)
    基本的にはHのみを操作する。
    [Note, Note, Note, ..., Note]
    """

    def __init__(self):
        super().__init__()
        self.contexts = ['xx'] * 2

    @property
    def number_of_syllables(self):
        """
        フレーズ内の音節数。

        _OneLine からSongを生成するときに使うかも。
        フレーズの切り替わり判定をするときに使うかも。
        多分使わない。
        """
        return self.contexts[0]

    @number_of_syllables.setter
    def number_of_syllables(self, number):
        self.contexts[0] = number

    @property
    def number_of_phonemes(self):
        """
        フレーズ内の音素数。
        _OneLine からSongを生成するときに使う。
        """
        return self.contexts[1]

    @number_of_phonemes.setter
    def number_of_phonemes(self, number):
        self.contexts[1] = number


class Note(list):
    """
    ノートまたは休符を扱うクラス
    1ノート（ノートと休符）を扱うクラス
    昨日のノート D (d1~d5)
    今日のノート E (e1~e60)
    明日のノート F (f1~f5)
    基本的にはEのみを操作する。
    [Syllable, Syllable, ..., Syllable]
    """

    def __init__(self):
        super().__init__()
        self.contexts = ['xx'] * 60

    @property
    def position(self):
        """
        フレーズ内での位置
        """
        return self.contexts[17]

    @position.setter
    def position(self, position: int):
        self.contexts[17] = int(position)


class Syllable(list):
    """
    1音節を扱うクラス
    昨日の音節 A (a1~a5)
    今日の音節 B (b1~b5)
    明日の音節 C (c1~c5)
    [Phoneme, Phoneme, ..., Phoneme]
    """

    def __init__(self):
        super().__init__()
        self.contexts = ['xx'] * 5

    @property
    def position(self):
        """
        ノート内での位置
        """
        return int(self.contexts[1])

    @position.setter
    def position(self, position: int):
        self.contexts[1] = position

    @property
    def number_of_phonemes(self):
        """
        音節内の音素数(b1)
        """
        return self.contexts[0]

    @number_of_phonemes.setter
    def number_of_phonemes(self, number: int):
        self.contexts[0] = number


class Phoneme:
    """
    音素を扱うクラス
    p1~p16
    """

    def __init__(self):
        # 発声開始時刻
        self.start: int = 0
        # 発声終了時刻
        self.end: int = 0
        # p1: 言語非依存の音素記号(p, c, v など)
        self.language_independent_identity: str = 'xx'
        # p4: 音素記号
        self.identity: str = 'xx'
        # p9: フラグ
        self.flag: str = 'xx'
        # p12: 音節(Syllable)内の、先頭から数えた位置
        self.position: int = 'xx'
        # p13: 音節(Syllable)内の、末尾から数えた位置
        self.position_backward: int = 'xx'
        # p14: 今が子音のときのみに定義される、直前の母音からの距離
        self.distance_from_previous_vowel: int = 'xx'
        # p15: 今が子音のときのみに定義される、直後の母音までの距離
        self.distance_to_next_vowel: int = 'xx'
        # 未定義のコンテキスト
        self.undefined_context = 'xx'

    def __str__(self):
        return f'{self.start} {self.end} {self.identity}'
