"""Portable pure/TEMP regression. Imports installed project sources; no business/UI calls."""
import sys,ast,copy,importlib.util,unittest,tempfile,json,os
from pathlib import Path
from unittest.mock import patch
R=next(p for p in Path(__file__).resolve().parents if (p/'skills/chrome-dom-export/scripts/review_capture.py').is_file() and (p/'packages/workshop-director/workshop_director/timing_worker.py').is_file())
sys.path[:0]=[str(R/'skills/workshop-director/scripts'),str(R/'skills/negative-review-complaints/scripts'),str(R/'skills/chrome-dom-export/scripts'),str(R/'skills/douyin-laike-operator/scripts'),str(R/'packages/workshop-director')]
import review_capture as rc
def n(label='',selector='#n',cls='',children=None):return {'name':label,'selector':selector,'attributes':{'class':cls},'children':children or []}
def root():
 head=n(selector='#header',cls='header-sQid1u commentListHeader-jKdTh_',children=[n('已筛选1条','#count')]);card=n('body','#card','commentItem-jrXo5p');total=n('共1条记录','#total','text-bjyZFG');prev=n(selector='#previous',cls='button-j4VxiA isDisabled-unTBS6');current=n('1/1','#current','text-bjyZFG');nxt=n(selector='#next',cls='button-j4VxiA isDisabled-unTBS6');group=n(selector='#group',cls='buttonGroup-GDbp9Y',children=[prev,current,nxt]);pager=n(selector='#pager',cls='pagination-GXvAPk',children=[total,group]);return n(selector='#root',children=[head,card,pager])
def checked(profile,value):
 rc.normal.complete_normal_list(value,1);pager=value['children'][-1];group=pager['children'][1];expected={'pager':pager,'total':pager['children'][0],'previous':group['children'][0],'current':group['children'][1],'next':group['children'][2]};return rc.complete_list_nodes(profile,value,expected)
class Tests(unittest.TestCase):

    def test_omitted_rules_derive_exact_existing_five_nodes_without_mutation(self):
        r = root()
        before = copy.deepcopy(r)
        profile = {'normal_root_exclusive': True}
        self.assertEqual({k: v['selector'] for (k, v) in checked(profile, r).items()}, {'pager': '#pager', 'total': '#total', 'previous': '#previous', 'current': '#current', 'next': '#next'})
        self.assertEqual(r, before)
        self.assertNotIn('complete_list', profile)

    def test_explicit_valid_rules_preserve_old_behavior(self):
        r = root()
        rules = {k: {'selector': v['selector']} for (k, v) in checked({}, r).items()}
        actual = checked({'complete_list': rules}, r)
        self.assertIs(actual['pager'], r['children'][-1])

    def test_explicit_missing_extra_none_wrong_rules_are_not_fallback(self):
        for value in ({}, None, {'wrong': {}}, {'pager': {'selector': '#card'}}):
            with self.assertRaises(ValueError):
                checked({'complete_list': value}, root())

    def test_explicit_same_five_keys_wrong_scope_rejected(self):
        r = root()
        rules = {k: {'selector': v['selector']} for (k, v) in checked({}, r).items()}
        rules['pager'] = {'selector': '#card'}
        with self.assertRaisesRegex(ValueError, 'position-mismatch'):
            checked({'complete_list': rules}, r)

    def test_missing_empty_or_nonstring_actual_selector_rejected(self):
        for selector in ('', None, True, ' '):
            r = root()
            r['children'][-1]['selector'] = selector
            with self.assertRaisesRegex(ValueError, 'selector-missing'):
                checked({}, r)

    def test_duplicate_actual_selector_rejected(self):
        r = root()
        r['children'][1]['children'].append(n(selector='#pager'))
        with self.assertRaises(ValueError):
            checked({}, r)

    def test_changed_total_page_or_enabled_button_rejected(self):
        for kind in ('total', 'current', 'button'):
            r = root()
            pager = r['children'][-1]
            if kind == 'total':
                pager['children'][0]['name'] = '共2条记录'
            elif kind == 'current':
                pager['children'][1]['children'][1]['name'] = '1/2'
            else:
                pager['children'][1]['children'][2]['attributes']['class'] = 'button-j4VxiA'
            with self.assertRaises(ValueError):
                checked({}, r)
    def test_current_command_consumes_checked_complete_list(self):
        import inspect
        tree=ast.parse(inspect.getsource(rc.command_from_inputs));calls=[n for n in ast.walk(tree) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='complete_list_nodes'];self.assertEqual(len(calls),1);self.assertEqual([ast.unparse(a) for a in calls[0].args],['profile','root','expected'])

if __name__=="__main__":unittest.main()
