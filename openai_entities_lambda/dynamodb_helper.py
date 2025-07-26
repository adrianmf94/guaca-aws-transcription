import boto3

class DynamoDBHelper:
    def __init__(self, table_name):
        self.table_name = table_name
        self.dynamodb = boto3.resource(
            'dynamodb',
        )
        self.table = self.dynamodb.Table(table_name)

    def insert_item(self, item):
        try:
            response = self.table.put_item(Item=item)
            print("Item inserted successfully:", response)
        except Exception as e:
            print("Error inserting item:", e)

