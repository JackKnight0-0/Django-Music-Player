from django.test import TestCase


class TestMixin(TestCase):

    def request_base_test(self, path, slug=None, pk=None, not_allowed_method=None, data=None, error_test=True,
                          method='get', status_code=200, request_model='default', template_used=None,
                          query_param=None):
        full_path = None
        request = None
        action = None
        not_valid_value = 'not_valid'

        if request_model == 'default':
            request = self.client
        else:
            request = request_model

        methods = {
            'get': request.get,
            'post': request.post,
            'put': request.put,
            'delete': request.delete,
            'patch': request.patch
        }

        action = methods.get(method)

        if slug is not None:
            full_path = path + str(slug) + '/'
            not_valid_value = 'not_valid@__32_-+1123#$@#!()*%(!_(@#)'
        elif pk is not None:
            full_path = path + str(pk) + '/'
            not_valid_value = '28379487392789324798324897324897928374'
        else:
            full_path = path

        if not_allowed_method:
            response_not_allowed = methods.get(not_allowed_method)(full_path)
            self.assertEqual(response_not_allowed.status_code, 405)
        if error_test:
            response_error = action(path + not_valid_value + '/')
            self.assertEqual(response_error.status_code, 404)

        if query_param is not None:
            for query in query_param.split():
                if full_path.endswith('/'):
                    full_path += '?q=' + query
                else:
                    full_path += '+' + query

        if data:
            response = action(full_path, data)
        else:
            response = action(full_path)

        if template_used is not None:
            self.assertTemplateUsed(response, template_used)

        self.assertEqual(response.status_code, status_code)

        return response

    def obj_logout_user_test(self, path, method, request_model, path_slug=None, path_pk=None,
                             expect_login_url='/account/login/'):
        request_model.logout()
        full_path = path
        request_data = {
            'path': path,
            'method': method,
            'error_test': False,
            'request_model': request_model,
            'status_code': 302,
        }

        if method in ['post', 'put', 'patch']:
            request_data['data'] = {'any': 'any'}

        if path_pk is not None:
            request_data['pk'] = path_pk
            full_path += str(path_pk) + '/'
        elif path_slug is not None:
            request_data['slug'] = path_slug
            full_path += str(path_slug) + '/'

        response = self.request_base_test(**request_data)
        url = expect_login_url + '?next=' + full_path
        self.assertEqual(response.url, url)
