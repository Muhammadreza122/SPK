
from http import HTTPStatus
from flask import Flask, request, abort
from flask_restful import Resource, Api 
from models import Coffe as CoffeModel
from engine import engine
from sqlalchemy import select
from sqlalchemy.orm import Session

session = Session(engine)

app = Flask(__name__)
api = Api(app)        

class BaseMethod():

    def __init__(self):
        self.raw_weight = {'rasa': 9, 'harga': 8, 'pelayanan': 4, 'suasana': 7, 'jarak': 5}

    @property
    def weight(self):
        total_weight = sum(self.raw_weight.values())
        return {k: round(v/total_weight, 2) for k, v in self.raw_weight.items()}

    @property
    def data(self):
        query = select(CoffeModel.id, CoffeModel.namatoko, CoffeModel.rasa, CoffeModel.harga, CoffeModel.pelayanan, CoffeModel.suasana, CoffeModel.jarak)
        result = session.execute(query).fetchall()
        print(result)
        return [{'id': CoffeeShop.id, 'namatoko': CoffeeShop.namatoko, 'rasa': CoffeeShop.rasa, 'harga': CoffeeShop.harga, 'pelayanan': CoffeeShop.pelayanan, 'suasana': CoffeeShop.suasana, 'jarak': CoffeeShop.jarak} for CoffeeShop in result]

    @property
    def normalized_data(self):
        rasa_values= []
        harga_values = []
        pelayanan_values = []
        suasana_values = []
        jarak_values = []


        for data in self.data:
            rasa_values.append(data['rasa'])
            harga_values.append(data['harga'])
            pelayanan_values.append(data['pelayanan'])
            suasana_values.append(data['suasana'])
            jarak_values.append(data['jarak'])

        return [
            {'id': data['id'],
             'namatoko': data['namatoko'],
             'rasa': data['rasa'] / max(rasa_values),
             'harga': min(harga_values) / data['harga'],
             'pelayanan': data['pelayanan'] / max(pelayanan_values),
             'suasana': data['suasana'] / max(suasana_values),
             'jarak': data['jarak'] / max(jarak_values)
             }
            for data in self.data
        ]

    def update_weights(self, new_weights):
        self.raw_weight = new_weights

class WeightedProductCalculator(BaseMethod):
    def update_weights(self, new_weights):
        self.raw_weight = new_weights

    @property
    def calculate(self):
        normalized_data = self.normalized_data
        produk = []

        for row in normalized_data:
            product_score = (
                row['rasa'] ** self.raw_weight['rasa'] *
                row['harga'] ** self.raw_weight['harga'] *
                row['pelayanan'] ** self.raw_weight['pelayanan'] *
                row['suasana'] ** self.raw_weight['suasana']*
                row['jarak'] ** self.raw_weight['jarak'] 
            )

            produk.append({
                'id': row['id'],
                'produk': product_score
            })

        sorted_produk = sorted(produk, key=lambda x: x['produk'], reverse=True)

        sorted_data = []

        for product in sorted_produk:
            sorted_data.append({
                'id': product['id'],
                'score': product['produk']
            })

        return sorted_data


class WeightedProduct(Resource):
    def get(self):
        calculator = WeightedProductCalculator()
        result = calculator.calculate
        return result, HTTPStatus.OK.value
    
    def post(self):
        new_weights = request.get_json()
        calculator = WeightedProductCalculator()
        calculator.update_weights(new_weights)
        result = calculator.calculate
        return {'data': result}, HTTPStatus.OK.value
    

class SimpleAdditiveWeightingCalculator(BaseMethod):
    @property
    def calculate(self):
        weight = self.weight
        result = {row['id']:
                  round(row['rasa'] * weight['rasa'] +
                        row['harga'] * weight['harga'] +
                        row['pelayanan'] * weight['pelayanan'] +
                        row['suasana'] * weight['suasana'] +
                        row['jarak'] * weight['jarak'], 2)
                  for row in self.normalized_data
                  }
        sorted_result = dict(
            sorted(result.items(), key=lambda x: x[1], reverse=True))
        return sorted_result

    def update_weights(self, new_weights):
        self.raw_weight = new_weights

class SimpleAdditiveWeighting(Resource):
    def get(self):
        saw = SimpleAdditiveWeightingCalculator()
        result = saw.calculate
        return result, HTTPStatus.OK.value

    def post(self):
        new_weights = request.get_json()
        saw = SimpleAdditiveWeightingCalculator()
        saw.update_weights(new_weights)
        result = saw.calculate
        return {'data': result}, HTTPStatus.OK.value


class Coffe(Resource):
    def get_paginated_result(self, url, list, args):
        page_size = int(args.get('page_size', 10))
        page = int(args.get('page', 1))
        page_count = int((len(list) + page_size - 1) / page_size)
        start = (page - 1) * page_size
        end = min(start + page_size, len(list))

        if page < page_count:
            next_page = f'{url}?page={page+1}&page_size={page_size}'
        else:
            next_page = None
        if page > 1:
            prev_page = f'{url}?page={page-1}&page_size={page_size}'
        else:
            prev_page = None
        
        if page > page_count or page < 1:
            abort(404, description=f'Halaman {page} tidak ditemukan.') 
        return {
            'page': page, 
            'page_size': page_size,
            'next': next_page, 
            'prev': prev_page,
            'Results': list[start:end]
        }

    def get(self):
        query = select(CoffeModel)
        data = [{'id': CoffeeShop.id, 'namatoko': CoffeeShop.namatoko, 'rasa': CoffeeShop.rasa, 'harga': CoffeeShop.harga, 'pelayanan': CoffeeShop.pelayanan, 'suasana': CoffeeShop.suasana, 'jarak': CoffeeShop.jarak} for CoffeeShop in session.scalars(query)]
        return self.get_paginated_result('CoffeeShop/', data, request.args), HTTPStatus.OK.value


api.add_resource(Coffe, '/CoffeeShop')
api.add_resource(WeightedProduct, '/wp')
api.add_resource(SimpleAdditiveWeighting, '/saw')

if __name__ == '__main__':
    app.run(port='5005', debug=True)
